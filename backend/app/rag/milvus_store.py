from pymilvus import Collection, utility
from app.rag.milvus_client import connect_milvus
from app.rag.embeddings import embed_text
from uuid import uuid4

from app.rag.milvus_schema import (
    COLLECTION_NAME,
    create_all_collections,
)


def insert_chunks(document_id: str, filename: str, chunks: list[str], page_number: int = 0):
    """Insert text chunks into unified collection."""
    connect_milvus()

    if not utility.has_collection(COLLECTION_NAME):
        create_all_collections()

    collection = Collection(COLLECTION_NAME)

    embeddings = [embed_text(c) for c in chunks]

    data = [
        [str(uuid4()) for _ in chunks],   # id
        [document_id] * len(chunks),      # document_id
        embeddings,                       # embedding
        chunks,                           # chunk_text
        [filename] * len(chunks),         # filename
        [page_number] * len(chunks),      # page_number
        [0] * len(chunks),                # table_index
        [0] * len(chunks),                # row_index
    ]

    collection.insert(data)
    collection.flush()


def insert_table_rows(document_id: str, filename: str, rows: list[dict]):
    """Insert table rows into unified collection."""
    if not rows:
        return

    connect_milvus()

    if not utility.has_collection(COLLECTION_NAME):
        create_all_collections()

    collection = Collection(COLLECTION_NAME)

    texts = [r["text"] for r in rows]
    embeddings = [embed_text(t) for t in texts]

    data = [
        [str(uuid4()) for _ in rows],                          # id
        [document_id] * len(rows),                             # document_id
        embeddings,                                            # embedding
        texts,                                                 # chunk_text
        [filename] * len(rows),                                # filename
        [int(r.get("page_number") or 0) for r in rows],       # page_number
        [int(r.get("table_index") or 0) for r in rows],       # table_index
        [int(r.get("row_index") or 0) for r in rows],         # row_index
    ]

    collection.insert(data)
    collection.flush()
