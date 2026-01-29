from app.rag.qa import answer_question
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from app.db.session import get_connection

from app.rag.chunking import chunk_text
from app.rag.embeddings import embed_text
from app.rag.milvus_store import insert_chunks
from app.rag.minio_client import get_minio_client

from uuid import uuid4
from app.rag.pdf_loader import extract_text_from_pdf
import io


import logging
import sys

# Configure logging at the module level or globally in main.py
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chatbot"])


# -------------------- MODELS --------------------

class StaticChatRequest(BaseModel):
    message: str
    session_id: str


class TreeChatRequest(BaseModel):
    value: str
    session_id: str
    
class TreeNodeCreate(BaseModel):
    value: str

class TreeEdgeCreate(BaseModel):
    from_node_id: str
    to_node_id: str


def get_tree_response(cur, node_id, value_fallback):
    cur.execute(
        """
        SELECT n.value
        FROM tree_edge e
        JOIN tree_node n ON n.id = e.to_node_id
        WHERE e.from_node_id = %s
        ORDER BY n.value
        """,
        (node_id,)
    )
    children = cur.fetchall()
    
    if len(children) == 0:
        return {"type": "text", "text": value_fallback}
    
    if len(children) == 1:
        return {"type": "text", "text": children[0][0]}

    return {
        "type": "buttons",
        "text": "Please choose an option:",
        "buttons": [
            {"label": c[0], "value": c[0]}
            for c in children
        ]
    }

def format_bot_log(response):
    text = response.get("text") or response.get("value") or ""
    buttons = response.get("buttons")
    if buttons:
        text += "\nOptions: " + ", ".join([b["label"] for b in buttons])
    return text



# -------------------- STATIC CHAT (TEXT INPUT) --------------------

@router.post("/message")
def static_chat(payload: StaticChatRequest):
    try:
        conn = get_connection()
        cur = conn.cursor()

        # 1. Log USER message
        cur.execute(
            """
            INSERT INTO chat_history (session_id, role, content)
            VALUES (%s, 'user', %s)
            """,
            (payload.session_id, payload.message)
        )

        # ... Helper to log assistant reply ...
        def log_and_return(response_dict):
            text_content = format_bot_log(response_dict)
            cur.execute(
                """
                INSERT INTO chat_history (session_id, role, content)
                VALUES (%s, 'assistant', %s)
                """,
                (payload.session_id, text_content)
            )
            conn.commit()
            cur.close()
            conn.close()
            return response_dict

        # Try STATIC first
        cur.execute(
            """
            SELECT child.value
            FROM node parent
            JOIN edge e ON e.from_node_id = parent.id
            JOIN node child ON child.id = e.to_node_id
            WHERE LOWER(parent.value) = LOWER(%s)
            LIMIT 1
            """,
            (payload.message,)
        )

        row = cur.fetchone()

        if row:
            return log_and_return({
                "type": "static",
                "text": row[0]
            })

        cur.execute(
            "SELECT id FROM tree_node WHERE LOWER(value) = LOWER(%s) LIMIT 1",
            (payload.message,)
        )

        node = cur.fetchone()

        if node:
            # DIRECTLY return tree response, no redirection
            tree_res = get_tree_response(cur, node[0], payload.message)
            return log_and_return(tree_res)
            
        rag_response = answer_question(payload.message)
        

        
        # Log token usage (Using print to ensure it appears in terminal)
        print(f"------------ RAG TOKEN STATS ------------")
        print(f"Session: {payload.session_id}")
        print(f"Prompt Tokens: {rag_response.get('prompt_tokens', 0)}")
        print(f"Response Tokens: {rag_response.get('response_tokens', 0)}")
        print(f"Total Tokens: {rag_response.get('total_tokens', 0)}")
        print(f"---------------------------------------")

        rag_text = rag_response["answer"]
        if rag_text != "No answer found in the document.":
            return log_and_return({"type": "rag", "text": rag_text})

        return log_and_return({
            "type": "none",
            "text": "Sorry, I don't understand."
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- TREE CHAT --------------------

@router.get("/tree/start")
def tree_start(session_id: str):
    conn = get_connection()
    cur = conn.cursor()

    # root nodes = nodes with no parent
    cur.execute(
        """
        SELECT n.id, n.value
        FROM tree_node n
        LEFT JOIN tree_edge e ON e.to_node_id = n.id
        WHERE e.to_node_id IS NULL
        ORDER BY n.value
        """
    )
    rows = cur.fetchall()

    response = {
        "type": "buttons",
        "text": "FAQs",
        "buttons": [{"label": r[1], "value": r[1]} for r in rows]
    }

    # Log the initial bot message
    cur.execute(
        """
        INSERT INTO chat_history (session_id, role, content)
        VALUES (%s, 'assistant', %s)
        """,
        (session_id, format_bot_log(response))
    )
    conn.commit()

    cur.close()
    conn.close()

    return response


@router.post("/tree/next")
def tree_next(payload: TreeChatRequest):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Log USER message (the button text clicked)
        cur.execute(
            """
            INSERT INTO chat_history (session_id, role, content)
            VALUES (%s, 'user', %s)
            """,
            (payload.session_id, payload.value)
        )
        conn.commit()

        # find clicked node
        cur.execute(
            "SELECT id FROM tree_node WHERE value = %s LIMIT 1",
            (payload.value,)
        )

        node = cur.fetchone()
        if not node:
            cur.close()
            conn.close()
            return {
                "type": "text",
                "text": "Invalid option."
            }

        node_id = node[0]
        response = get_tree_response(cur, node_id, payload.value)
        
        # Log ASSISTANT response
        cur.execute(
            """
            INSERT INTO chat_history (session_id, role, content)
            VALUES (%s, 'assistant', %s)
            """,
            (payload.session_id, format_bot_log(response))
        )
        conn.commit()
        
        return response

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()
    
@router.post("/tree/node")
def create_tree_node(payload: TreeNodeCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO tree_node (value)
        VALUES (%s)
        RETURNING id, value
        """,
        (payload.value,)
    )

    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return {
        "id": row[0],
        "value": row[1]
    }


@router.post("/tree/edge")
def create_tree_edge(payload: TreeEdgeCreate):
    conn = get_connection()
    cur = conn.cursor()

    # optional: basic validation
    cur.execute(
        "SELECT id FROM tree_node WHERE id = %s",
        (payload.from_node_id,)
    )
    if not cur.fetchone():
        raise HTTPException(status_code=400, detail="Invalid from_node_id")

    cur.execute(
        "SELECT id FROM tree_node WHERE id = %s",
        (payload.to_node_id,)
    )
    if not cur.fetchone():
        raise HTTPException(status_code=400, detail="Invalid to_node_id")

    cur.execute(
        """
        INSERT INTO tree_edge (from_node_id, to_node_id)
        VALUES (%s, %s)
        RETURNING id
        """,
        (payload.from_node_id, payload.to_node_id)
    )

    edge_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return {
        "id": edge_id,
        "from_node_id": payload.from_node_id,
        "to_node_id": payload.to_node_id
    }

@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # 1️⃣ Read PDF bytes
    pdf_bytes = await file.read()

    # 2️⃣ Extract text
    full_text = extract_text_from_pdf(pdf_bytes)

    if not full_text.strip():
        raise HTTPException(status_code=400, detail="No text found in PDF")

    # 3️⃣ Chunk text (generic, works for any PDF)
    chunks = chunk_text(full_text)

    if not chunks:
        raise HTTPException(status_code=400, detail="Chunking failed")

    # Log chunk stats
    avg_chars = sum(len(c) for c in chunks) / len(chunks) if chunks else 0
    logger.info(f"PDF processed: {len(chunks)} chunks created.")
    logger.info(f"Average chunk details: {avg_chars:.1f} characters (approx {avg_chars/4:.1f} tokens).")

    # 4️⃣ Upload PDF to MinIO
    minio = get_minio_client()
    bucket = "documents"

    if not minio.bucket_exists(bucket):
        minio.make_bucket(bucket)

    object_name = f"{uuid4()}_{file.filename}"
    minio.put_object(
        bucket_name=bucket,
        object_name=object_name,
        data=io.BytesIO(pdf_bytes),
        length=len(pdf_bytes),
        content_type="application/pdf",
    )

    # 5️⃣ Store chunks in Milvus
    document_id = str(uuid4())

    insert_chunks(
        document_id=document_id,
        filename=file.filename,
        chunks=chunks,
    )

    return {
        "status": "success",
        "filename": file.filename,
        "chunks": len(chunks),
    }