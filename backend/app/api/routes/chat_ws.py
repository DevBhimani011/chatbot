from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.redis import get_redis_client
from app.core.queue import get_mq_client
from app.db.session import get_connection
from app.core.config import settings
import jwt
import json
import asyncio
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# ... (WebSocketHandler class remains same) ...

class WebSocketHandler:
    def __init__(self, websocket: WebSocket, session_id: str):
        self.websocket = websocket
        self.session_id = session_id
        self.channel_name = f"chat_channel_{session_id}"
        self.redis_client = None
        self.mq_client = None
        self.pubsub = None
        self.listener_task = None
    
    async def connect(self):
        await self.websocket.accept()
        logger.info(f"🔌 WebSocket connected: {self.session_id}")
        
        self.redis_client = get_redis_client()
        self.mq_client = await get_mq_client()
        
        self.pubsub = self.redis_client.pubsub()
        await asyncio.to_thread(self.pubsub.subscribe, self.channel_name)
        logger.info(f"👂 Subscribed to Redis channel: {self.channel_name}")
        
        try:
            await self.websocket.send_text("CONNECTED")
            logger.info(f"✅ Sent connection confirmation to {self.session_id}")
        except Exception as e:
            logger.error(f"❌ Failed to send connection confirmation: {e}")
            raise e

    async def listen_to_redis(self):
        try:
            while True:
                message = await asyncio.to_thread(self.pubsub.get_message, ignore_subscribe_messages=True)
                if message and message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode('utf-8')
                        
                    logger.info(f"📨 Received from Redis: {data}")
                    try:
                        await self.websocket.send_text(data)
                    except Exception as e:
                        logger.error(f"❌ Failed to send message to WebSocket: {e}")
                        break
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            logger.info(f"🛑 Redis listener cancelled for {self.session_id}")
        except Exception as e:
            logger.error(f"❌ Redis listener error: {e}")

    def _check_static_response(self, message: str):
        """Sync method to check Redis and DB"""
        # 1. Check Redis
        try:
            cache_key = f"chat_hash:{hash(message.strip().lower())}"
            if self.redis_client:
                cached_val = self.redis_client.get(cache_key)
                if cached_val:
                    logger.info(f"🚀 [SOURCE: REDIS] Cache HIT for static query: '{message}'")
                    return cached_val
        except Exception as e:
            logger.error(f"⚠️ Redis error in static check: {e}")

        # 2. Check DB
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT child.value
                FROM node parent
                JOIN edge e ON e.from_node_id = parent.id
                JOIN node child ON child.id = e.to_node_id
                WHERE LOWER(parent.value) = LOWER(%s)
                LIMIT 1
                """,
                (message,)
            )
            row = cur.fetchone()
            if row:
                response_text = row[0]
                logger.info(f"💾 [SOURCE: DATABASE - STATIC] Found answer for: '{message}' -> Caching to Redis")
                try:
                    if self.redis_client:
                        self.redis_client.setex(cache_key, 600, response_text)
                        logger.info(f"📦 [CACHE] Stored static response in Redis (TTL: 600s)")
                except Exception as e:
                    logger.error(f"⚠️ Failed to cache to Redis: {e}")
                return response_text
            return None
        except Exception as e:
            logger.error(f"Error in static check: {e}")
            return None
        finally:
            cur.close()
            conn.close()

    async def run(self):
        try:
            await self.connect()
            self.listener_task = asyncio.create_task(self.listen_to_redis())
            
            while True:
                data = await self.websocket.receive_text()
                logger.info(f"👤 User sent: {data}")
                
                # Run sync static check in thread
                static_reply = await asyncio.to_thread(self._check_static_response, data)
                
                if static_reply:
                    await self.websocket.send_text(static_reply)
                    continue

                # Publish to RAG
                payload = {
                    "session_id": self.session_id,
                    "message": data
                }
                await self.mq_client.publish_message("chat_queue", payload)

        except WebSocketDisconnect:
            logger.info(f"🔌 WebSocket disconnected: {self.session_id}")
        except Exception as e:
            logger.error(f"❌ WebSocket error: {e}")
        finally:
            await self.cleanup()

    async def cleanup(self):
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
        
        if self.pubsub:
            try:
                await asyncio.to_thread(self.pubsub.unsubscribe, self.channel_name)
                await asyncio.to_thread(self.pubsub.close)
            except Exception as e:
                logger.error(f"❌ Cleanup error: {e}")

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, token: str = Query(...)):
    """
    WebSocket endpoint with Query Param Authentication
    Usage: ws://host/chat/ws/{session_id}?token=JWT_TOKEN
    """
    # 1. Validate Token
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            logger.warning(f"❌ WebSocket Auth Failed: No user_id in token")
            await websocket.close(code=4003) # Forbidden
            return
    except Exception as e:
        logger.error(f"❌ WebSocket Auth Failed: {e}")
        await websocket.close(code=4003)
        return

    # 2. Proceed if valid
    handler = WebSocketHandler(websocket, session_id)
    await handler.run()
