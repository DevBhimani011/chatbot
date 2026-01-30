from pymilvus import Collection, utility
from app.rag.milvus_client import connect_milvus
from app.rag.embeddings import embed_text
from uuid import uuid4

from app.rag.milvus_schema import (
    TEXT_COLLECTION_NAME,
    TABLE_ROWS_COLLECTION_NAME,
    create_all_collections,
)


def insert_chunks(document_id: str, filename: str, chunks: list[str]):
    # 🔑 ENSURE CONNECTION
    connect_milvus()

    if not utility.has_collection(TEXT_COLLECTION_NAME):
        create_all_collections()

    collection = Collection(TEXT_COLLECTION_NAME)

    embeddings = [embed_text(c) for c in chunks]

    data = [
        [str(uuid4()) for _ in chunks],   # chunk_id
        [document_id] * len(chunks),      # document_id
        embeddings,                       # vector
        chunks,                           # chunk_text
        [filename] * len(chunks),         # filename
    ]

    collection.insert(data)
    collection.flush()


def insert_table_rows(document_id: str, filename: str, rows: list[dict]):
    if not rows:
        return

    connect_milvus()

    if not utility.has_collection(TABLE_ROWS_COLLECTION_NAME):
        create_all_collections()

    collection = Collection(TABLE_ROWS_COLLECTION_NAME)

    texts = [r["text"] for r in rows]
    embeddings = [embed_text(t) for t in texts]

    data = [
        [str(uuid4()) for _ in rows],
        [document_id] * len(rows),
        embeddings,
        texts,
        [filename] * len(rows),
        [int(r.get("page_number") or 0) for r in rows],
        [int(r.get("table_index") or 0) for r in rows],
        [int(r.get("row_index") or 0) for r in rows],
    ]

    collection.insert(data)
    collection.flush()
