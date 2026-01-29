from app.core.config import settings
from pymilvus import Collection, connections
from app.rag.embeddings import embed_text


def search_similar_chunks(query: str, limit: int = 5):
    # Ensure Milvus connection exists
    connections.connect(
        alias="default",
        host=settings.MILVUS_HOST,
        port=settings.MILVUS_PORT
    )

    collection = Collection("document_chunks")
    collection.load()

    query_vector = embed_text(query)

    search_params = {
        "metric_type": "COSINE",
        "params": {"nprobe": 10},
    }

    results = collection.search(
        data=[query_vector],
        anns_field="embedding",
        param=search_params,
        limit=limit,
        output_fields=["chunk_text", "filename"],
    )

    matches = []
    for hit in results[0]:
        matches.append({
            "similarity": hit.score,
            "text": hit.entity.get("chunk_text"),
            "filename": hit.entity.get("filename"),
        })

    return matches
