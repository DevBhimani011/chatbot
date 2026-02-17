"""
Dedicated Document Worker Process
Handles PDF processing tasks from pdf_queue
Separated from chat workers for better resource isolation and independent scaling
"""
import asyncio
import logging
import sys
import os
from app.workers.document_worker import DocumentWorkerService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def main():
    """Run document worker only"""
    logger.info("🚀 Starting Dedicated Document Worker Process")
    doc_worker = DocumentWorkerService()
    await doc_worker.run()

if __name__ == "__main__":
    asyncio.run(main())
