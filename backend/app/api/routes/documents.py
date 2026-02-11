from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.rag.minio_client import get_minio_client
from app.rag.milvus_client import connect_milvus
from pymilvus import Collection
from app.core.queue import get_mq_client
from uuid import uuid4
from urllib.parse import quote
import io
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


class DocumentInfo(BaseModel):
    object_name: str
    filename: str
    size: int
    last_modified: str


@router.get("/list")
def list_documents():
    """List all documents stored in MinIO"""
    logger.info("📋 Listing all documents from MinIO")
    try:
        client = get_minio_client()
        bucket = "documents"
        
        if not client.bucket_exists(bucket):
            logger.warning(f"⚠️ Bucket '{bucket}' does not exist")
            return {"documents": []}
        
        objects = client.list_objects(bucket)
        documents = []
        
        for obj in objects:
            # Skip files that are still processing
            if obj.object_name.startswith("processing/"):
                continue
                
            documents.append({
                "object_name": obj.object_name,
                "filename": obj.object_name.split("_", 1)[1] if "_" in obj.object_name else obj.object_name,
                "size": obj.size,
                "last_modified": obj.last_modified.isoformat()
            })
        
        logger.info(f"✅ Successfully listed {len(documents)} documents")
        return {"documents": documents}
    
    except Exception as e:
        logger.error(f"❌ Error listing documents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{object_name:path}")
def download_document(object_name: str):
    """Download or view a document from MinIO"""
    logger.info(f"📥 Downloading document: {object_name}")
    try:
        client = get_minio_client()
        bucket = "documents"
        
        if not client.bucket_exists(bucket):
            logger.error(f"❌ Bucket '{bucket}' not found")
            raise HTTPException(status_code=404, detail="Bucket not found")
        
        # Get object from MinIO
        response = client.get_object(bucket, object_name)
        
        # Read the data
        file_data = response.read()
        response.close()
        response.release_conn()
        
        # Extract filename from object_name
        filename = object_name.split("_", 1)[1] if "_" in object_name else object_name
        
        logger.info(f"✅ Successfully retrieved document: {filename}")
        
        # Encode filename for Content-Disposition header (RFC 5987)
        # Use ASCII-safe encoding for the filename
        encoded_filename = quote(filename)
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
            }
        )
    
    except Exception as e:
        logger.error(f"❌ Error downloading document {object_name}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{object_name:path}")
def delete_document(object_name: str):
    """Delete document from MinIO and all related chunks from Milvus"""
    logger.info(f"🗑️ Deleting document: {object_name}")
    try:
        # Extract document_id from object_name (format: {uuid}_{filename})
        document_id = object_name.split("_")[0] if "_" in object_name else None
        logger.info(f"📝 Extracted document_id: {document_id}")
        
        # 1️⃣ Delete from MinIO
        client = get_minio_client()
        bucket = "documents"
        
        if not client.bucket_exists(bucket):
            logger.error(f"❌ Bucket '{bucket}' not found")
            raise HTTPException(status_code=404, detail="Bucket not found")
        
        client.remove_object(bucket, object_name)
        logger.info(f"✅ Deleted from MinIO: {object_name}")
        
        # 2️⃣ Delete from Milvus (all chunks with this document_id)
        if document_id:
            try:
                logger.info(f"🔍 Connecting to Milvus to delete chunks for document_id: {document_id}")
                connect_milvus()
                # Delete all chunks with this document_id from both collections
                expr = f'document_id == "{document_id}"'
                logger.info(f"🗑️ Executing Milvus delete with expression: {expr}")

                for collection_name in ["document_chunks", "document_table_rows"]:
                    try:
                        collection = Collection(collection_name)
                        collection.load()
                        collection.delete(expr)
                        collection.flush()
                    except Exception as delete_error:
                        logger.warning(
                            f"⚠️ Error deleting from {collection_name}: {str(delete_error)}",
                            exc_info=True,
                        )
                
                logger.info(f"✅ Successfully deleted chunks from Milvus for document_id: {document_id}")
            except Exception as milvus_error:
                logger.warning(f"⚠️ Error deleting from Milvus: {str(milvus_error)}", exc_info=True)
                # Continue even if Milvus deletion fails
        
        logger.info(f"🎉 Document deletion completed successfully: {object_name}")
        return {
            "status": "success",
            "message": f"Document {object_name} deleted successfully"
        }
    
    except Exception as e:
        logger.error(f"❌ Error deleting document {object_name}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload PDF and queue for processing"""
    logger.info(f"📤 Uploading PDF: {file.filename}")
    
    if not file.filename.lower().endswith(".pdf"):
        logger.warning(f"⚠️ Invalid file type attempted: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        # 1️⃣ Read PDF bytes
        logger.info(f"📖 Reading PDF bytes from: {file.filename}")
        pdf_bytes = await file.read()
        logger.info(f"✅ Read {len(pdf_bytes)} bytes")

        # 2️⃣ Generate document_id
        document_id = str(uuid4())
        logger.info(f"🆔 Generated document_id: {document_id}")

        # 3️⃣ Upload PDF to MinIO
        logger.info(f"☁️ Uploading to MinIO: {file.filename}")
        minio = get_minio_client()
        bucket = "documents"

        if not minio.bucket_exists(bucket):
            logger.info(f"📦 Creating bucket: {bucket}")
            minio.make_bucket(bucket)

        # Prepend 'processing/' directory to hidden it from list
        object_name = f"processing/{document_id}_{file.filename}"
        
        minio.put_object(
            bucket_name=bucket,
            object_name=object_name,
            data=io.BytesIO(pdf_bytes),
            length=len(pdf_bytes),
            content_type="application/pdf",
        )
        logger.info(f"✅ Uploaded to MinIO as: {object_name}")

        # 4️⃣ Enqueue Task
        logger.info(f"📨 Queueing processing task for: {file.filename}")
        mq = await get_mq_client()
        await mq.publish_message("pdf_queue", {
            "document_id": document_id,
            "filename": file.filename,
            "object_name": object_name
        })

        return {
            "status": "processing",
            "message": "PDF upload accepted and processing started",
            "document_id": document_id,
            "filename": file.filename,
            "object_name": object_name
        }
    
    except Exception as e:
        logger.error(f"❌ Error uploading PDF {file.filename}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

