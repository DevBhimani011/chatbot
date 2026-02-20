from pymilvus import (
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    utility,
)
from app.rag.milvus_client import connect_milvus

COLLECTION_NAME = "document_chunks"
DIMENSION = 1024  # intfloat/e5-large-v2


def create_collection():
    """Create unified collection for all document content (text and tables)."""
    connect_milvus()

    if utility.has_collection(COLLECTION_NAME):
        print(f"Collection {COLLECTION_NAME} already exists. Skipping creation.")
        return

    fields = [
        FieldSchema(
            name="id",
            dtype=DataType.VARCHAR,
            is_primary=True,
            max_length=64,
        ),
        FieldSchema(
            name="document_id",
            dtype=DataType.VARCHAR,
            max_length=64,
        ),
        FieldSchema(
            name="embedding",
            dtype=DataType.FLOAT_VECTOR,
            dim=DIMENSION,
        ),
        FieldSchema(
            name="chunk_text",
            dtype=DataType.VARCHAR,
            max_length=8192,  # Increased for larger markdown chunks/tables
        ),
        FieldSchema(
            name="filename",
            dtype=DataType.VARCHAR,
            max_length=256,
        ),
        FieldSchema(
            name="page_number",
            dtype=DataType.INT64,
            default_value=0,
        ),
        FieldSchema(
            name="table_index",
            dtype=DataType.INT64,
            default_value=0,
        ),
        FieldSchema(
            name="row_index",
            dtype=DataType.INT64,
            default_value=0,
        ),
    ]

    schema = CollectionSchema(fields, description="Unified RAG document chunks")
    collection = Collection(COLLECTION_NAME, schema)

    # index for fast search
    collection.create_index(
        field_name="embedding",
        index_params={
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128},
        },
    )

    print("Milvus unified collection created successfully")


def create_all_collections():
    """Alias for backward compatibility."""
    create_collection()


if __name__ == "__main__":
    create_all_collections()



if __name__ == "__main__":
    create_all_collections()
