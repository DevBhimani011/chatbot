import asyncio
import logging
import json
import sys
import io
from app.core.config import settings
from app.core.redis import get_redis_client
from aio_pika import connect, IncomingMessage
from app.rag.minio_client import get_minio_client
from app.rag.pdf_loader import extract_text_and_tables_from_pdf
from app.rag.chunking import chunk_text, table_rows_to_chunks
from app.rag.milvus_store import insert_chunks, insert_table_rows
from minio.commonconfig import CopySource

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

class DocumentWorkerService:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.redis_client = None

    async def connect(self):
        """Establish RabbitMQ connection"""
        self.connection = await connect(settings.RABBITMQ_URL)
        self.channel = await self.connection.channel()
        await self.channel.declare_queue("pdf_queue", durable=True)
        self.redis_client = get_redis_client()
        logger.info("✅ Connected to RabbitMQ & Redis Client initialized")

    async def process_message(self, message: IncomingMessage):
        """Handle incoming tasks"""
        # Manual acknowledgment pattern to ensure we don't block the loop
        try:
            document_id = None
            filename = "Unknown"
            
            body = message.body.decode()
            data = json.loads(body)
            document_id = data.get("document_id")
            filename = data.get("filename")
            object_name = data.get("object_name")
            
            logger.info(f"📨 Received PDF task: {filename} ({document_id})")
            


            # 1. Download from MinIO (Sync)
            logger.info(f"⬇️ Downloading from MinIO: {object_name}")
            def download_file():
                minio = get_minio_client()
                bucket = "documents"
                response = minio.get_object(bucket, object_name)
                data = response.read()
                response.close()
                response.release_conn()
                return data

            pdf_bytes = await asyncio.to_thread(download_file)
            
            # 2. Extract Text/Tables (Sync & CPU Intensive)
            logger.info(f"🔍 Extracting text and tables from: {filename}")
            pages_text, tables = await asyncio.to_thread(extract_text_and_tables_from_pdf, pdf_bytes)
            full_text = "\n\n".join(pages_text.values())

            if not full_text.strip() and not tables:
                logger.warning(f"⚠️ No text or tables found in: {filename}")
            
            # Handle tables if text is empty
            if not full_text.strip() and tables:
                logger.info("Converting tables to text format (no regular text found)")
                table_texts = []
                for table_data in tables:
                    table_str = f"Table (Page {table_data.get('page_number', 'unknown')}):\n"
                    table = table_data.get('rows', [])
                    if table:
                        if len(table) > 0:
                            headers = table[0]
                            table_str += " | ".join(str(h) for h in headers) + "\n"
                            table_str += "-" * (len(headers) * 10) + "\n"
                        for row in table[1:] if len(table) > 1 else table:
                            table_str += " | ".join(str(cell) for cell in row) + "\n"
                    table_texts.append(table_str)
                full_text = "\n\n".join(table_texts)

            # 3. Chunk Text (Sync)
            logger.info(f"✂️ Chunking text...")
            chunks = await asyncio.to_thread(chunk_text, full_text)
            
            # 4. Insert to Milvus (Sync & Network Blocking)
            if chunks:
                logger.info(f"💾 Storing {len(chunks)} text chunks in Milvus")
                await asyncio.to_thread(
                    insert_chunks,
                    document_id=document_id,
                    filename=filename,
                    chunks=chunks
                )
            
            # 5. Insert Tables (Sync)
            if tables:
                table_rows = table_rows_to_chunks(tables)
                if table_rows:
                    logger.info(f"💾 Storing {len(table_rows)} table rows in Milvus")
                    await asyncio.to_thread(
                        insert_table_rows,
                        document_id=document_id,
                        filename=filename,
                        rows=table_rows
                    )

            logger.info(f"✅ PDF processing completed: {filename}")
            
            # 6. Promote file from processing/ to root (Sync)
            logger.info(f"🚚 Promoting file to active storage: {object_name}")
            def promote_file():
                minio = get_minio_client()
                bucket = "documents"
                
                # New object name (remove processing/ prefix)
                new_object_name = object_name.replace("processing/", "", 1)
                
                # Copy object using CopySource
                minio.copy_object(
                    bucket,
                    new_object_name,
                    CopySource(bucket, object_name)
                )
                
                # Remove original
                minio.remove_object(bucket, object_name)
                return new_object_name

            await asyncio.to_thread(promote_file)
            logger.info(f"✅ File promoted successfully")
            


            # Acknowledge message only after successful processing
            await message.ack()

        except Exception as e:
            logger.error(f"❌ Error processing PDF: {e}", exc_info=True)

            
            # Reject message (don't requeue if it's a permanent error)
            await message.reject(requeue=False)

    async def run(self):
        logger.info("👷 Document Worker Service Starting...")
        try:
            await self.connect()
            queue = await self.channel.get_queue("pdf_queue")
            logger.info("✅ Document Worker Ready over RabbitMQ")
            await queue.consume(self.process_message)
            await asyncio.Future()  # Keep running
        except Exception as e:
            logger.error(f"❌ Worker crashed: {e}", exc_info=True)
            await asyncio.sleep(5)

async def main():
    service = DocumentWorkerService()
    await service.run()

if __name__ == "__main__":
    asyncio.run(main())
