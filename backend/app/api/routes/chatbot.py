from fastapi import APIRouter
from pydantic import BaseModel
from app.db.session import get_connection

router = APIRouter(prefix="/chat", tags=["Chatbot"])


# -------------------- MODELS --------------------

class StaticChatRequest(BaseModel):
    message: str


class TreeChatRequest(BaseModel):
    value: str
    
class TreeNodeCreate(BaseModel):
    value: str

class TreeEdgeCreate(BaseModel):
    from_node_id: str
    to_node_id: str



# -------------------- STATIC CHAT (TEXT INPUT) --------------------

@router.post("/static")
def static_chat(payload: StaticChatRequest):
    conn = get_connection()
    cur = conn.cursor()

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
        cur.close()
        conn.close()
        return {
            "type": "static",
            "text": row[0]
        }

    cur.execute(
        "SELECT id FROM tree_node WHERE LOWER(value) = LOWER(%s) LIMIT 1",
        (payload.message,)
    )

    node = cur.fetchone()
    cur.close()
    conn.close()

    if node:
        return {
            "type": "faq",
            "value": payload.message
        }

    return {
        "type": "none",
        "text": "Sorry, I don't understand."
    }


# -------------------- TREE CHAT --------------------

@router.get("/tree/start")
def tree_start():
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
    cur.close()
    conn.close()

    return {
        "type": "buttons",
        "text": "FAQs",
        "buttons": [
            {"label": r[1], "value": r[1]}
            for r in rows
        ]
    }


@router.post("/tree/next")
def tree_next(payload: TreeChatRequest):
    conn = get_connection()
    cur = conn.cursor()

    # find clicked node
    cur.execute(
        "SELECT id FROM tree_node WHERE value = %s LIMIT 1",
        (payload.value,)
    )

    node = cur.fetchone()
    if not node:
        return {
            "type": "text",
            "text": "Invalid option."
        }

    node_id = node[0]

    # get children
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
    cur.close()
    conn.close()

    if len(children) == 0:
        return {
            "type": "text",
            "text": payload.value
        }

    if len(children) == 1:
        return {
            "type": "text",
            "text": children[0][0]
        }

    return {
        "type": "buttons",
        "text": "Please choose an option:",
        "buttons": [
            {"label": c[0], "value": c[0]}
            for c in children
        ]
    }
    
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
