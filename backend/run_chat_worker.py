"""
Dedicated Chat Worker Process
Handles chat messages from chat_queue
Separated from document workers for better resource isolation
"""
import asyncio
import logging
import sys
import os
from app.workers.chat_worker import WorkerService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def main():
    """Run chat worker only"""
    logger.info("🚀 Starting Dedicated Chat Worker Process")
    chat_worker = WorkerService()
    await chat_worker.run()

if __name__ == "__main__":
    asyncio.run(main())
