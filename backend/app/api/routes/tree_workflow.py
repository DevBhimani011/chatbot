from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID
from app.db.session import get_connection

router = APIRouter(prefix="/tree-workflows", tags=["FAQ Workflows"])

class TreeWorkflowCreate(BaseModel):
    name: str

class TreeNodeCreate(BaseModel):
    tree_workflow_id: UUID
    value: str
    position_x: float | None = None
    position_y: float | None = None

class TreeNodeUpdate(BaseModel):
    value: str

class TreeEdgeCreate(BaseModel):
    tree_workflow_id: UUID
    from_node_id: UUID
    to_node_id: UUID
    
class TreeNodePositionUpdate(BaseModel):
    position_x: float
    position_y: float

@router.post("/nodes")
def create_tree_node(payload: TreeNodeCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO tree_node (tree_workflow_id, value, position_x, position_y)
        VALUES (%s, %s, %s, %s)
        RETURNING id, value, position_x, position_y
        """,
        (
            str(payload.tree_workflow_id),
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
        "value": row[1],
        "position_x": row[2],
        "position_y": row[3],
    }

@router.patch("/nodes/{node_id}/position")
def update_tree_node_position(node_id: UUID, payload: TreeNodePositionUpdate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE tree_node
        SET position_x=%s, position_y=%s
        WHERE id=%s
        """,
        (payload.position_x, payload.position_y, str(node_id)),
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"status": "position_updated"}

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

# @router.post("/nodes")
# def create_tree_node(payload: TreeNodeCreate):
#     conn = get_connection()
#     cur = conn.cursor()

#     cur.execute(
#         """
#         INSERT INTO tree_node (tree_workflow_id, value)
#         VALUES (%s, %s)
#         RETURNING id, value
#         """,
#         (str(payload.tree_workflow_id), payload.value)
#     )

#     row = cur.fetchone()
#     conn.commit()
#     cur.close()
#     conn.close()

#     return {
#         "id": row[0],
#         "value": row[1]
#     }


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

@router.delete("/nodes/{node_id}")
def delete_tree_node(node_id: UUID):
    conn = get_connection()
    cur = conn.cursor()

    # delete connected edges first
    cur.execute(
        """
        DELETE FROM tree_edge
        WHERE from_node_id = %s OR to_node_id = %s
        """,
        (str(node_id), str(node_id)),
    )

    # delete node
    cur.execute(
        """
        DELETE FROM tree_node
        WHERE id = %s
        """,
        (str(node_id),)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {
        "status": "tree_node_deleted",
        "id": str(node_id)
    }

@router.delete("/edges/{edge_id}")
def delete_tree_edge(edge_id: UUID):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM tree_edge WHERE id = %s",
        (str(edge_id),)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {
        "status": "tree_edge_deleted",
        "id": str(edge_id)
    }

@router.delete("/{tree_workflow_id}")
def delete_tree_workflow(tree_workflow_id: UUID):
    conn = get_connection()
    cur = conn.cursor()

    # 1️⃣ delete edges
    cur.execute(
        """
        DELETE FROM tree_edge
        WHERE tree_workflow_id = %s
        """,
        (str(tree_workflow_id),)
    )

    # 2️⃣ delete nodes
    cur.execute(
        """
        DELETE FROM tree_node
        WHERE tree_workflow_id = %s
        """,
        (str(tree_workflow_id),)
    )

    # 3️⃣ delete workflow
    cur.execute(
        """
        DELETE FROM tree_workflow
        WHERE id = %s
        """,
        (str(tree_workflow_id),)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {
        "status": "tree_workflow_deleted",
        "id": str(tree_workflow_id)
    }

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
        (payload.name,),
    )

    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return {
        "id": row[0],
        "name": row[1],
    }
