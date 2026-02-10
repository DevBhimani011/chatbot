from aio_pika import connect, Message, DeliveryMode
from app.core.config import settings
import json
import logging

logger = logging.getLogger(__name__)

class RabbitMQClient:
    def __init__(self):
        self.connection = None
        self.channel = None

    async def connect(self):
        """Establish connection to RabbitMQ"""
        if not self.connection or self.connection.is_closed:
            try:
                self.connection = await connect(settings.RABBITMQ_URL)
                self.channel = await self.connection.channel()
                # Declare the queue to ensure it exists
                await self.channel.declare_queue("chat_queue", durable=True)
                logger.info("✅ Connected to RabbitMQ")
            except Exception as e:
                logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
                raise e

    async def publish_message(self, queue_name: str, message: dict):
        """Publish a message to a specific queue"""
        if not self.channel or self.channel.is_closed:
            await self.connect()

        try:
            await self.channel.default_exchange.publish(
                Message(
                    body=json.dumps(message).encode(),
                    delivery_mode=DeliveryMode.PERSISTENT
                ),
                routing_key=queue_name
            )
            logger.info(f"📤 Published message to {queue_name}: {message.get('session_id')}")
        except Exception as e:
            logger.error(f"❌ Failed to publish message: {e}")
            raise e

    async def close(self):
        if self.connection and not self.connection.is_closed:
            await self.connection.close()

# Global instance
mq_client = RabbitMQClient()

async def get_mq_client():
    if not mq_client.connection or mq_client.connection.is_closed:
        await mq_client.connect()
    return mq_client
