import asyncio
import logging
import json
import sys
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from app.core.config import settings
from app.db.session import get_connection
from aio_pika import connect, IncomingMessage
from app.rag.chunking import chunk_text
from app.rag.milvus_store import insert_chunks
import psycopg2

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

class CrawlerWorkerService:
    def __init__(self):
        self.connection = None
        self.channel = None

    async def connect(self):
        """Establish RabbitMQ connection"""
        self.connection = await connect(settings.RABBITMQ_URL)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)
        await self.channel.declare_queue("crawler_queue", durable=True)
        logger.info("✅ Connected to RabbitMQ (Crawler Worker)")

    async def update_status(self, url_id, status, error_msg=None):
        def _update():
            conn = get_connection()
            cur = conn.cursor()
            try:
                now = datetime.now() if status == 'completed' else None
                if status == 'completed':
                    cur.execute(
                        "UPDATE crawled_url SET status = %s, last_crawled_at = %s WHERE id = %s",
                        (status, now, str(url_id))
                    )
                else:
                    # If failed, maybe store error? For now, just status.
                    cur.execute(
                        "UPDATE crawled_url SET status = %s WHERE id = %s",
                        (status, str(url_id))
                    )
                conn.commit()
            except Exception as e:
                logger.error(f"Failed to update status for {url_id}: {e}")
            finally:
                cur.close()
                conn.close()
        
        await asyncio.to_thread(_update)

    async def fetch_url(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=30, ssl=False) as response:
                if response.status == 403:
                    logger.warning(f"⚠️ 403 Forbidden for {url}. Trying with different headers...")
                    # Fallback mechanism could go here, but for now just logging specific error
                
                response.raise_for_status()
                return await response.text()

    def parse_html(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator='\n')
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text

    async def process_message(self, message: IncomingMessage):
        """Handle incoming crawl tasks"""
        try:
            body = message.body.decode()
            data = json.loads(body)
            url_id = data.get("url_id")
            url = data.get("url")
            
            logger.info(f"🕸️ Received crawl task: {url} ({url_id})")
            
            # 1. Update status to processing
            await self.update_status(url_id, "processing")

            # 2. Fetch URL
            logger.info(f"⬇️ Fetching URL: {url}")
            try:
                html = await self.fetch_url(url)
            except Exception as e:
                logger.error(f"❌ Failed to fetch URL {url}: {e}")
                await self.update_status(url_id, "failed")
                await message.reject(requeue=False)
                return

            # 3. Parse HTML (CPU bound)
            logger.info(f"🔍 Parsing HTML...")
            text = await asyncio.to_thread(self.parse_html, html)

            if not text:
                logger.warning(f"⚠️ No text found in: {url}")
                await self.update_status(url_id, "failed") # Or completed with warning?
                await message.reject(requeue=False) # Or ack?
                return

            # 4. Chunk Text
            logger.info(f"✂️ Chunking text...")
            chunks = await asyncio.to_thread(chunk_text, text)
            
            # 5. Insert to Milvus
            if chunks:
                logger.info(f"💾 Storing {len(chunks)} chunks in Milvus")
                # Use url_id as document_id for consistency
                await asyncio.to_thread(
                    insert_chunks,
                    document_id=str(url_id),
                    filename=url, # Use URL as filename
                    chunks=chunks
                )

            # 6. Update status to completed
            await self.update_status(url_id, "completed")
            logger.info(f"✅ Crawl completed: {url}")
            
            await message.ack()

        except Exception as e:
            logger.error(f"❌ Error processing crawl task: {e}", exc_info=True)
            if url_id:
                await self.update_status(url_id, "failed")
            await message.reject(requeue=False)

    async def run(self):
        logger.info("🕷️ Crawler Worker Service Starting...")
        try:
            await self.connect()
            queue = await self.channel.get_queue("crawler_queue")
            logger.info("✅ Crawler Worker Ready")
            await queue.consume(self.process_message)
            await asyncio.Future()
        except Exception as e:
            logger.error(f"❌ Worker crashed: {e}", exc_info=True)
            await asyncio.sleep(5)

async def main():
    service = CrawlerWorkerService()
    await service.run()

if __name__ == "__main__":
    asyncio.run(main())
