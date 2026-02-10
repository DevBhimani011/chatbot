import asyncio
import logging
import json
import sys
from app.core.config import settings
from app.core.redis import get_redis_client
from aio_pika import connect, IncomingMessage
from app.rag.qa import answer_question

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
                logger.info(f"📡 Publishing to Redis channel: {channel_name}")
                self.redis_client.publish(channel_name, "Analyzing documents...")
                
                # --- RAG PIPELINE ---
                response_generator = answer_question(user_message)
                
                full_answer = ""
                
                if isinstance(response_generator, dict):
                    # Handle static error or "No answer found" cases
                    text = response_generator.get("answer", "")
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
