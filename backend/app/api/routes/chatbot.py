from app.rag.qa import answer_question
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from app.db.session import get_connection

from app.rag.chunking import chunk_text
from app.rag.embeddings import embed_text
from app.rag.milvus_store import insert_chunks
from app.rag.minio_client import get_minio_client
from app.core.redis import get_redis_client
import json

from uuid import uuid4
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
            
            # Re-obtain connection if closed (shouldn't happen here but safe check)
            # Actually we reuse 'cur' from outer scope.
            
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

        # ---------------- Check Redis Cache ----------------
        redis_client = get_redis_client()
        cache_key = f"chat_hash:{hash(payload.message.strip().lower())}"
        
        if redis_client:
            cached_val = redis_client.get(cache_key)
            if cached_val:
                logger.info(f"🚀 [SOURCE: REDIS] Cache HIT for query: '{payload.message}'")
                return log_and_return(json.loads(cached_val))

        # ---------------- Try STATIC ----------------
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
            logger.info(f"💾 [SOURCE: DATABASE - STATIC] Found answer for: '{payload.message}' -> Caching to Redis")
            response_dict = {
                "type": "static",
                "text": row[0]
            }
            # Cache it
            if redis_client:
                redis_client.setex(cache_key, 600, json.dumps(response_dict))
                logger.info(f"📦 [CACHE] Stored static response in Redis (TTL: 600s)")
                
            return log_and_return(response_dict)

        # ---------------- Try TREE / FAQ ----------------
        cur.execute(
            "SELECT id FROM tree_node WHERE LOWER(value) = LOWER(%s) LIMIT 1",
            (payload.message,)
        )

        node = cur.fetchone()

        if node:
            logger.info(f"🌳 [SOURCE: DATABASE - FAQ] Found tree node for: '{payload.message}' -> Caching to Redis")
            # DIRECTLY return tree response
            tree_res = get_tree_response(cur, node[0], payload.message)
            
            # Cache it
            if redis_client:
                redis_client.setex(cache_key, 600, json.dumps(tree_res))
                logger.info(f"📦 [CACHE] Stored FAQ response in Redis (TTL: 600s)")
                
            return log_and_return(tree_res)
            
        # ---------------- RAG Fallback (No Caching) ----------------
        logger.info(f"🤖 [SOURCE: RAG] Attempting RAG generation for: '{payload.message}'")
        rag_response = answer_question(payload.message)

        
        # Log token usage
        print(f"------------ RAG TOKEN STATS ------------")
        print(f"Session: {payload.session_id}")
        print(f"Prompt Tokens: {rag_response.get('prompt_tokens', 0)}")
        print(f"Response Tokens: {rag_response.get('response_tokens', 0)}")
        print(f"Total Tokens: {rag_response.get('total_tokens', 0)}")
        print(f"---------------------------------------")

        rag_text = rag_response["answer"]
        if rag_text != "No answer found in the document.":
            # NOTE: We specifically DO NOT CACHE RAG responses for now
            return log_and_return({"type": "rag", "text": rag_text})

        return log_and_return({
            "type": "none",
            "text": "Sorry, I don't understand."
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        if 'cur' in locals() and not cur.closed:
            cur.close()
        if 'conn' in locals() and not conn.closed:
            conn.close()
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

        # ---------------- Check Redis Cache ----------------
        redis_client = get_redis_client()
        cache_key = f"chat_hash:{hash(payload.value.strip().lower())}"

        if redis_client:
            cached_val = redis_client.get(cache_key)
            if cached_val:
                logger.info(f"🚀 [SOURCE: REDIS] Cache HIT for button: '{payload.value}'")
                
                # We need to log the assistant response even if it comes from cache
                response = json.loads(cached_val)
                cur.execute(
                    """
                    INSERT INTO chat_history (session_id, role, content)
                    VALUES (%s, 'assistant', %s)
                    """,
                    (payload.session_id, format_bot_log(response))
                )
                conn.commit()
                
                return response

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
        logger.info(f"🌳 [SOURCE: DATABASE - FAQ] Found tree node for button: '{payload.value}' -> Caching to Redis")
        
        response = get_tree_response(cur, node_id, payload.value)
        
        # Cache it
        if redis_client:
            redis_client.setex(cache_key, 600, json.dumps(response))
            logger.info(f"📦 [CACHE] Stored FAQ response in Redis (TTL: 600s)")
        
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
