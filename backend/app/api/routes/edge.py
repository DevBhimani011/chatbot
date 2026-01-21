from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID
from app.db.session import get_connection

router = APIRouter(prefix="/edges", tags=["Edges"])

class EdgeCreate(BaseModel):
    workflow_id: UUID
    from_node_id: UUID
    to_node_id: UUID

@router.post("/")
def create_edge(payload: EdgeCreate):
    conn = get_connection()
    cur = conn.cursor()

    # Optional safety check: prevent self-link
    if payload.from_node_id == payload.to_node_id:
        raise HTTPException(status_code=400, detail="Cannot link node to itself")

    cur.execute(
        """
        INSERT INTO edge (workflow_id, from_node_id, to_node_id)
        VALUES (%s, %s, %s)
        RETURNING id, workflow_id, from_node_id, to_node_id
        """,
        (
            str(payload.workflow_id),
            str(payload.from_node_id),
            str(payload.to_node_id)
        )
    )

    result = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()

    return {
        "id": result[0],
        "workflow_id": result[1],
        "from_node_id": result[2],
        "to_node_id": result[3]
    }
    
@router.get("/workflow/{workflow_id}")
def get_workflow_edges(workflow_id: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, workflow_id, from_node_id, to_node_id
        FROM edge
        WHERE workflow_id = %s
        """,
        (workflow_id,)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "id": row[0],
            "workflow_id": row[1],
            "from_node_id": row[2],
            "to_node_id": row[3]
        }
        for row in rows
    ]
    
@router.delete("/{edge_id}")
def delete_edge(edge_id: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM edge WHERE id = %s", (edge_id,))

    conn.commit()
    cur.close()
    conn.close()

    return {"status": "edge_deleted", "id": edge_id}
