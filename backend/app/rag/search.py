from app.core.config import settings
from pymilvus import Collection, connections
from app.rag.embeddings import embed_query

from app.rag.milvus_schema import COLLECTION_NAME


def search_similar_chunks(query: str, limit: int = 5):
    """Search for similar chunks in unified collection."""
    connections.connect(
        alias="default",
        host=settings.MILVUS_HOST,
        port=settings.MILVUS_PORT
    )

    query_vector = embed_query(query)

    search_params = {
        "metric_type": "COSINE",
        "params": {"nprobe": 10},
    }

    try:
        collection = Collection(COLLECTION_NAME)
        collection.load()
        results = collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=limit,
            output_fields=["chunk_text", "filename", "page_number", "table_index", "row_index"],
        )
        
        matches = []
        for hit in results[0]:
            matches.append({
                "similarity": hit.score,
                "text": hit.entity.get("chunk_text"),
                "filename": hit.entity.get("filename"),
                "page_number": hit.entity.get("page_number"),
                "table_index": hit.entity.get("table_index"),
                "row_index": hit.entity.get("row_index"),
            })
        
        return matches
    except Exception as e:
        print(f"Search error: {e}")
        return []
