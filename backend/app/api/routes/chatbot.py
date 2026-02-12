from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.db.session import get_connection
from app.core.redis import get_redis_client
from app.api.deps import get_current_user
import json
import logging
import sys


# Configure logging at the module level or globally in main.py
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chatbot"], dependencies=[Depends(get_current_user)])


# -------------------- MODELS --------------------

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

# -------------------- TREE CHAT --------------------

@router.get("/suggestions")
def get_suggestions(query: str):
    conn = get_connection()
    cur = conn.cursor()
    
    # Simple ILIKE search for suggestions
    cur.execute(
        """
        SELECT DISTINCT value
        FROM (
            -- Questions from Workflow (Node -> Edge)
            SELECT n.value
            FROM node n
            JOIN edge e ON n.id = e.from_node_id
            WHERE n.value ILIKE %s
            
            UNION
            
            -- Questions from Tree Workflow (TreeNode -> TreeEdge)
            SELECT tn.value
            FROM tree_node tn
            JOIN tree_edge te ON tn.id = te.from_node_id
            WHERE tn.value ILIKE %s
        ) AS suggestions
        ORDER BY value
        LIMIT 5
        """,
        (f"%{query}%", f"%{query}%")
    )
    
    rows = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return [r[0] for r in rows]

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
        "text": "Want to know about:",
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