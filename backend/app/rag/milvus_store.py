from pymilvus import Collection
from app.rag.milvus_client import connect_milvus
from app.rag.embeddings import embed_text
from uuid import uuid4


def insert_chunks(document_id: str, filename: str, chunks: list[str]):
    # 🔑 ENSURE CONNECTION
    connect_milvus()

    collection = Collection("document_chunks")

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
