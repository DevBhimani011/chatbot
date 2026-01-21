from fastapi import APIRouter
from pydantic import BaseModel
from uuid import UUID
from app.db.session import get_connection

router = APIRouter(prefix="/nodes", tags=["Nodes"])

class NodeCreate(BaseModel):
    workflow_id: UUID
    value: str
    position_x: float | None = None
    position_y: float | None = None

class NodeUpdate(BaseModel):
    value: str

class NodePositionUpdate(BaseModel):
    position_x: float
    position_y: float


@router.post("/")
def create_node(payload: NodeCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO node (workflow_id, value, position_x, position_y)
        VALUES (%s, %s, %s, %s)
        RETURNING id, workflow_id, value, position_x, position_y
        """,
        (
            str(payload.workflow_id),
            payload.value,
            payload.position_x,
            payload.position_y,
        ),
    )

    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return {
        "id": row[0],
        "workflow_id": row[1],
        "value": row[2],
        "position_x": row[3],
        "position_y": row[4],
    }


@router.patch("/{node_id}")
def update_node(node_id: UUID, payload: NodeUpdate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE node SET value=%s WHERE id=%s",
        (payload.value, str(node_id)),
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"status": "updated"}


@router.patch("/{node_id}/position")
def update_node_position(node_id: UUID, payload: NodePositionUpdate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE node
        SET position_x = %s, position_y = %s
        WHERE id = %s
        """,
        (payload.position_x, payload.position_y, str(node_id)),
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"status": "position_updated"}


@router.delete("/{node_id}")
def delete_node(node_id: UUID):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM edge WHERE from_node_id=%s OR to_node_id=%s",
        (str(node_id), str(node_id)),
    )
    cur.execute("DELETE FROM node WHERE id=%s", (str(node_id),))

    conn.commit()
    cur.close()
    conn.close()

    return {"status": "node_deleted", "id": str(node_id)}
