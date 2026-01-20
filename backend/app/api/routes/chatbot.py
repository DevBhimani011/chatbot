from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db.session import get_connection

router = APIRouter(prefix="/chat", tags=["Chatbot"])

class ChatRequest(BaseModel):
    message: str

@router.post("/")
def chat(payload: ChatRequest):
    conn = get_connection()
    cur = conn.cursor()

    # 1. Find matching parent node
    cur.execute(
        """
        SELECT id
        FROM node
        WHERE LOWER(value) = LOWER(%s)
        LIMIT 1
        """,
        (payload.message,)
    )

    parent = cur.fetchone()

    if not parent:
        return {"reply": "Sorry, I don't understand."}

    parent_id = parent[0]

    # 2. Find child node
    cur.execute(
        """
        SELECT n.value
        FROM edge e
        JOIN node n ON e.to_node_id = n.id
        WHERE e.from_node_id = %s
        LIMIT 1
        """,
        (parent_id,)
    )

    child = cur.fetchone()
    cur.close()
    conn.close()

    if not child or not child[0]:
        return {"reply": "Sorry, I don't have a response for that yet."}

    return {"reply": child[0]}
