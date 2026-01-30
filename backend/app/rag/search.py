from app.core.config import settings
from pymilvus import Collection, connections
from app.rag.embeddings import embed_text

from app.rag.milvus_schema import TEXT_COLLECTION_NAME, TABLE_ROWS_COLLECTION_NAME


def _escape_milvus_string(value: str) -> str:
    # Milvus expressions use double quotes for strings. Escape backslashes and quotes.
    return value.replace("\\", "\\\\").replace('"', "\\\"")


def search_similar_chunks(query: str, limit: int = 5):
    # Ensure Milvus connection exists
    connections.connect(
        alias="default",
        host=settings.MILVUS_HOST,
        port=settings.MILVUS_PORT
    )

    query_vector = embed_text(query)

    search_params = {
        "metric_type": "COSINE",
        "params": {"nprobe": 10},
    }

    matches = []

    # Search narrative text chunks
    try:
        text_collection = Collection(TEXT_COLLECTION_NAME)
        text_collection.load()
        text_results = text_collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=limit,
            output_fields=["chunk_text", "filename"],
        )
        for hit in text_results[0]:
            matches.append({
                "similarity": hit.score,
                "text": hit.entity.get("chunk_text"),
                "filename": hit.entity.get("filename"),
                "source": "text",
            })
    except Exception:
        pass

    # Search table rows (header-aware)
    try:
        table_collection = Collection(TABLE_ROWS_COLLECTION_NAME)
        table_collection.load()
        table_results = table_collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=limit,
            output_fields=["chunk_text", "filename", "page_number", "table_index", "row_index"],
        )
        for hit in table_results[0]:
            matches.append({
                "similarity": hit.score,
                "text": hit.entity.get("chunk_text"),
                "filename": hit.entity.get("filename"),
                "source": "table",
                "page_number": hit.entity.get("page_number"),
                "table_index": hit.entity.get("table_index"),
                "row_index": hit.entity.get("row_index"),
            })
    except Exception:
        pass

    matches.sort(key=lambda m: m.get("similarity", 0), reverse=True)
    return matches[:limit]


def query_table_rows_like(substring: str, limit: int = 10):
    """Fetch table-row chunks where chunk_text contains a substring.

    This is a high-precision fallback for table lookups (e.g., find a person's row).
    """
    if not substring or not substring.strip():
        return []

    # Ensure Milvus connection exists
    connections.connect(
        alias="default",
        host=settings.MILVUS_HOST,
        port=settings.MILVUS_PORT,
    )

    table_collection = Collection(TABLE_ROWS_COLLECTION_NAME)
    table_collection.load()

    safe = _escape_milvus_string(substring.strip())
    expr = f'chunk_text like "%{safe}%"'

    rows = table_collection.query(
        expr=expr,
        output_fields=["chunk_text", "filename", "page_number", "table_index", "row_index", "document_id"],
        limit=limit,
    )

    return [
        {
            "similarity": 1.0,
            "text": r.get("chunk_text"),
            "filename": r.get("filename"),
            "source": "table_exact",
            "page_number": r.get("page_number"),
            "table_index": r.get("table_index"),
            "row_index": r.get("row_index"),
            "document_id": r.get("document_id"),
        }
        for r in (rows or [])
        if r.get("chunk_text")
    ]
