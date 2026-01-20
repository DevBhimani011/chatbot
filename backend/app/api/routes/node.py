from fastapi import APIRouter
from pydantic import BaseModel
from uuid import UUID
from app.db.session import get_connection
from typing import Optional

router = APIRouter(prefix="/nodes", tags=["Nodes"])

class NodeCreate(BaseModel):
    workflow_id: UUID
    value: str


class NodeUpdate(BaseModel):
    value: str

    
@router.post("/")
def create_node(payload: NodeCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO node (workflow_id, value)
        VALUES (%s, %s)
        RETURNING id, workflow_id, value
        """,
        (str(payload.workflow_id), payload.value)
    )

    result = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return {
        "id": result[0],
        "workflow_id": result[1],
        "value": result[2],
    }


@router.patch("/{node_id}")
def update_node(node_id: str, payload: NodeUpdate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE node SET value=%s WHERE id=%s",
        (payload.value, node_id),
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"status": "updated"}
