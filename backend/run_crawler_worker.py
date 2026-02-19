"""
Dedicated Crawler Worker Process
Handles URL crawling tasks from crawler_queue
"""
import asyncio
import logging
import sys
from app.workers.crawler_worker import CrawlerWorkerService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def main():
    """Run crawler worker only"""
    logger.info("🚀 Starting Dedicated Crawler Worker Process")
    crawler_worker = CrawlerWorkerService()
    await crawler_worker.run()

if __name__ == "__main__":
    asyncio.run(main())
