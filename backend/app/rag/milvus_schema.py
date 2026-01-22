from pymilvus import (
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
)
from app.rag.milvus_client import connect_milvus

COLLECTION_NAME = "document_chunks"
DIMENSION = 384  # all-MiniLM-L6-v2


def create_collection():
    connect_milvus()

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
            max_length=2000,
        ),
        FieldSchema(
            name="filename",
            dtype=DataType.VARCHAR,
            max_length=256,
        ),
    ]

    schema = CollectionSchema(fields, description="RAG document chunks")
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

    print("Milvus collection created successfully")


if __name__ == "__main__":
    create_collection()
