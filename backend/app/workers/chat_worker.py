import asyncio
import logging
import json
import sys
from app.core.config import settings
from app.core.redis import get_redis_client
from aio_pika import connect, IncomingMessage
from app.rag.qa import answer_question
from app.db.session import get_connection

def check_database_for_answer(query: str):
    """
    Check if the query matches a known node or tree_node value.
    Returns the answer if found, otherwise None.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # 1. Check 'node' table (exact match or close match)
        # 1. Check 'node' table (match Question)
        cur.execute("SELECT id, value FROM node WHERE value ILIKE %s LIMIT 1", (query,))
        row = cur.fetchone()
        if row:
            node_id, node_value = row
            logger.info(f"✅ Found match in 'node' table (Question): {node_value}")
            
            # Find the Answer node connected via Edge
            cur.execute(
                """
                SELECT n.value 
                FROM edge e
                JOIN node n ON n.id = e.to_node_id
                WHERE e.from_node_id = %s
                LIMIT 1
                """, 
                (node_id,)
            )
            answer_row = cur.fetchone()
            
            if answer_row:
                logger.info(f"➡️ Found linked Answer: {answer_row[0]}")
                return {"type": "text", "text": answer_row[0]}
            else:
                logger.warning(f"⚠️ Found Question '{node_value}' but no linked Answer in 'edge' table.")
                # Fallback? Maybe return the question itself if no answer? Or None to let RAG handle it?
                # User wants "find from questions only". If it's a question with no answer, maybe it's incomplete.
                # Let's return None to allow RAG to try.
                return None

            
        # 2. Check 'tree_node' table
        cur.execute("SELECT id, value FROM tree_node WHERE value ILIKE %s LIMIT 1", (query,))
        row = cur.fetchone()
        if row:
            node_id, node_value = row
            logger.info(f"✅ Found match in 'tree_node' table: {node_value}")
            
            # Fetch children
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
            
            if not children:
                # Leaf node implies it is an answer, not a question.
                # User wants to search/match ONLY questions.
                logger.info(f"🍃 Found 'tree_node' '{node_value}' but it has no children (Leaf). Ignoring.")
                return None
            
            if len(children) == 1:
                # Single child: return child's value
                return {"type": "text", "text": children[0][0]}

            # Multiple children: return buttons
            return {
                "type": "buttons",
                "text": "Please choose an option:",
                "buttons": [
                    {"label": c[0], "value": c[0]}
                    for c in children
                ]
            }
            
        return None
    except Exception as e:
        logger.error(f"Error checking database: {e}")
        return None
    finally:
        cur.close()
        conn.close()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

class WorkerService:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.redis_client = None

    async def connect(self):
        """Establish RabbitMQ connection"""
        self.connection = await connect(settings.RABBITMQ_URL)
        self.channel = await self.connection.channel()
        
        # Set prefetch count to 1 to prevent worker from fetching all messages at once
        # This enables fair distribution across multiple workers
        await self.channel.set_qos(prefetch_count=1)
        
        await self.channel.declare_queue("chat_queue", durable=True)
        self.redis_client = get_redis_client()
        logger.info("✅ Connected to RabbitMQ & Redis Client initialized")

    async def process_message(self, message: IncomingMessage):
        """Handle incoming tasks"""
        async with message.process():
            session_id = None
            try:
                body = message.body.decode()
                data = json.loads(body)
                session_id = data.get("session_id")
                user_message = data.get("message")
                
                logger.info(f"📨 Received task for session: {session_id}")
                logger.info(f"💬 Processing message: {user_message}")
                
                if not self.redis_client:
                     logger.error("❌ Redis client not available")
                     return

                # Notify user that we are thinking
                channel_name = f"chat_channel_{session_id}"
                #logger.info(f"📡 Publishing to Redis channel: {channel_name}")
                #self.redis_client.publish(channel_name, "Thinking...")

                # --- HYBRID SEARCH PIPELINE ---
                
                # 1. DATABASE CHECK (Node & Tree Node)
                # We do this inside a thread to avoid blocking the async loop
                db_answer = await asyncio.to_thread(check_database_for_answer, user_message)
                
                if db_answer:
                    # Found a direct match in DB
                    logger.info(f"🚀 Database Hit! Returning direct answer.")
                    
                    # If it's a dict (structured response), dump to JSON
                    if isinstance(db_answer, dict):
                         response_text = json.dumps(db_answer)
                    else:
                         response_text = str(db_answer)
                         
                    self.redis_client.publish(channel_name, response_text)
                    full_answer = response_text
                    # Skip RAG
                    response_generator = None 
                else:
                    # 2. RAG FALLBACK
                    self.redis_client.publish(channel_name, "Analyzing documents...")
                    response_generator = answer_question(user_message)
                
                if response_generator:
                    full_answer = ""
                    
                    if isinstance(response_generator, dict):
                        # Handle static error or "No answer found" cases
                        text = response_generator.get("answer", "")
                        if text:
                            logger.info(f"📤 Publishing static response: {text[:50]}...")
                            self.redis_client.publish(channel_name, text)
                            full_answer = text
                    
                    else:
                        # Handle Streaming Response (generator)
                        chunk_count = 0
                        for chunk in response_generator:
                            if isinstance(chunk, str):
                                chunk_count += 1
                                self.redis_client.publish(channel_name, chunk)
                                full_answer += chunk
                        logger.info(f"📤 Published {chunk_count} chunks to Redis")
                
                logger.info(f"✅ Task completed. Answer length: {len(full_answer)}")

            except Exception as e:
                logger.error(f"❌ Error processing message: {e}", exc_info=True)
                if self.redis_client and session_id:
                     self.redis_client.publish(f"chat_channel_{session_id}", "Sorry, an internal error occurred.")

    async def run(self):
        logger.info("👷 Worker Service Starting...")
        try:
            await self.connect()
            queue = await self.channel.get_queue("chat_queue")
            logger.info("✅ Worker Service Ready over RabbitMQ")
            await queue.consume(self.process_message)
            await asyncio.Future()  # Keep running
        except Exception as e:
            logger.error(f"❌ Worker crashed: {e}", exc_info=True)
            await asyncio.sleep(5)

async def main():
    service = WorkerService()
    await service.run()

if __name__ == "__main__":
    asyncio.run(main())
