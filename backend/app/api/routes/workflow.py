from fastapi import APIRouter
from pydantic import BaseModel
from app.db.session import get_connection

router = APIRouter(prefix="/workflows", tags=["Workflows"])





@router.get("/")
def list_workflows():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM workflow")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {"id": row[0], "name": row[1]}
        for row in rows
    ]

@router.get("/{workflow_id}/nodes")
def get_workflow_nodes(workflow_id: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, value, position_x, position_y
        FROM node
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
            "value": row[1],
            "position_x": row[2],
            "position_y": row[3]
        }
        for row in rows
    ]

@router.delete("/{workflow_id}")
def delete_workflow(workflow_id: str):
    conn = get_connection()
    cur = conn.cursor()

    # 1. Delete edges of this workflow
    cur.execute(
        """
        DELETE FROM edge
        WHERE workflow_id = %s
        """,
        (workflow_id,)
    )

    # 2. Delete nodes of this workflow
    cur.execute(
        """
        DELETE FROM node
        WHERE workflow_id = %s
        """,
        (workflow_id,)
    )

    # 3. Delete workflow itself
    cur.execute(
        """
        DELETE FROM workflow
        WHERE id = %s
        """,
        (workflow_id,)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {
        "status": "deleted",
        "workflow_id": workflow_id
    }
