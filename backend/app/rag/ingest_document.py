from uuid import uuid4
import tempfile
import shutil

from app.rag.pdf_loader import extract_text_and_tables_from_pdf
from app.rag.chunking import chunk_text, table_rows_to_chunks
from app.rag.milvus_store import insert_chunks, insert_table_rows
from app.rag.minio_client import upload_pdf

def ingest_pdf(file):
    document_id = str(uuid4())
    filename = file.filename

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    # 1️⃣ Upload to MinIO
    upload_pdf(tmp_path, f"{document_id}_{filename}")

    # 2️⃣ Extract text AND tables in ONE pass (no duplication!)
    pages_text, tables = extract_text_and_tables_from_pdf(tmp_path)

    # 3️⃣ Chunk the non-table text
    combined_text = "\n\n".join(pages_text.values())
    text_chunks = chunk_text(combined_text) if combined_text.strip() else []

    # 4️⃣ Store text chunks in Milvus
    if text_chunks:
        insert_chunks(document_id, filename, text_chunks)

    # 5️⃣ Convert and store table rows
    table_rows = table_rows_to_chunks(tables)
    insert_table_rows(document_id=document_id, filename=filename, rows=table_rows)

    return {
        "document_id": document_id,
        "chunks": len(text_chunks),
        "table_rows": len(table_rows),
        "filename": filename,
    }
