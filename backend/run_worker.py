import asyncio
from app.workers.chat_worker import WorkerService as ChatWorkerService
from app.workers.document_worker import DocumentWorkerService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("🚀 Starting all workers...")
    
    chat_worker = ChatWorkerService()
    doc_worker = DocumentWorkerService()
    
    try:
        await asyncio.gather(
            chat_worker.run(),
            doc_worker.run()
        )
    except Exception as e:
        logger.error(f"❌ Worker process failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
