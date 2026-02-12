from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from uuid import UUID
from app.db.session import get_connection
from app.api.deps import get_current_user, get_current_admin_user

router = APIRouter(prefix="/workflows", tags=["Workflows"], dependencies=[Depends(get_current_admin_user)])

# ==================== MODELS ====================

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

class EdgeCreate(BaseModel):
    workflow_id: UUID
    from_node_id: UUID
    to_node_id: UUID


# ==================== WORKFLOW ENDPOINTS ====================

@router.get("/")
def list_workflows():
    """List all workflows"""
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
    """Get all nodes for a workflow"""
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


@router.get("/{workflow_id}/edges")
def get_workflow_edges(workflow_id: str):
    """Get all edges for a workflow"""
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


@router.delete("/{workflow_id}")
def delete_workflow(workflow_id: str):
    """Delete a workflow and all its nodes and edges"""
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


# ==================== NODE ENDPOINTS ====================

@router.post("/nodes")
def create_node(payload: NodeCreate):
    """Create a new node in a workflow"""
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


@router.patch("/nodes/{node_id}")
def update_node(node_id: UUID, payload: NodeUpdate):
    """Update node value"""
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


@router.patch("/nodes/{node_id}/position")
def update_node_position(node_id: UUID, payload: NodePositionUpdate):
    """Update node position"""
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


@router.delete("/nodes/{node_id}")
def delete_node(node_id: UUID):
    """Delete a node and its connected edges"""
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


# ==================== EDGE ENDPOINTS ====================

@router.post("/edges")
def create_edge(payload: EdgeCreate):
    """Create a new edge between two nodes"""
    conn = get_connection()
    cur = conn.cursor()

    # Safety check: prevent self-link
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


@router.delete("/edges/{edge_id}")
def delete_edge(edge_id: str):
    """Delete an edge"""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM edge WHERE id = %s", (edge_id,))

    conn.commit()
    cur.close()
    conn.close()

    return {"status": "edge_deleted", "id": edge_id}
