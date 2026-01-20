from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID
from app.db.session import get_connection

router = APIRouter(prefix="/tree-workflows", tags=["FAQ Workflows"])


# ======================================================
# MODELS
# ======================================================

class TreeWorkflowCreate(BaseModel):
    name: str


class TreeNodeCreate(BaseModel):
    tree_workflow_id: UUID
    value: str


class TreeNodeUpdate(BaseModel):
    value: str


class TreeEdgeCreate(BaseModel):
    tree_workflow_id: UUID
    from_node_id: UUID
    to_node_id: UUID


# ======================================================
# TREE WORKFLOW
# ======================================================

@router.post("/")
def create_tree_workflow(payload: TreeWorkflowCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO tree_workflow (name)
        VALUES (%s)
        RETURNING id, name
        """,
        (payload.name,)
    )

    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return {
        "id": row[0],
        "name": row[1]
    }


@router.get("/")
def list_tree_workflows():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, name
        FROM tree_workflow
        ORDER BY created_at DESC
        """
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {"id": r[0], "name": r[1]}
        for r in rows
    ]


# ======================================================
# TREE NODES
# ======================================================

@router.post("/nodes")
def create_tree_node(payload: TreeNodeCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO tree_node (tree_workflow_id, value)
        VALUES (%s, %s)
        RETURNING id, value
        """,
        (str(payload.tree_workflow_id), payload.value)
    )

    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return {
        "id": row[0],
        "value": row[1]
    }


@router.get("/{tree_workflow_id}/nodes")
def get_tree_nodes(tree_workflow_id: UUID):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, value
        FROM tree_node
        WHERE tree_workflow_id = %s
        """,
        (str(tree_workflow_id),)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {"id": r[0], "value": r[1]}
        for r in rows
    ]


@router.patch("/nodes/{node_id}")
def update_tree_node(node_id: UUID, payload: TreeNodeUpdate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE tree_node
        SET value = %s
        WHERE id = %s
        """,
        (payload.value, str(node_id)),
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"status": "updated"}


# ======================================================
# TREE EDGES
# ======================================================

@router.post("/edges")
def create_tree_edge(payload: TreeEdgeCreate):
    if payload.from_node_id == payload.to_node_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot connect a node to itself"
        )

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO tree_edge (tree_workflow_id, from_node_id, to_node_id)
        VALUES (%s, %s, %s)
        RETURNING id
        """,
        (
            str(payload.tree_workflow_id),
            str(payload.from_node_id),
            str(payload.to_node_id)
        )
    )

    edge_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return {"id": edge_id}


@router.get("/{tree_workflow_id}/edges")
def get_tree_edges(tree_workflow_id: UUID):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, from_node_id, to_node_id
        FROM tree_edge
        WHERE tree_workflow_id = %s
        """,
        (str(tree_workflow_id),)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "id": r[0],
            "from_node_id": r[1],
            "to_node_id": r[2]
        }
        for r in rows
    ]
