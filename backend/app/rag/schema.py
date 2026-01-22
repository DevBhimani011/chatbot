from pymilvus import (
    FieldSchema, CollectionSchema, DataType, Collection
)
from app.rag.milvus_client import connect_milvus

COLLECTION_NAME = "document_chunks"

def create_collection():
    connect_milvus()

    fields = [
        FieldSchema(
            name="id",
            dtype=DataType.VARCHAR,
            is_primary=True,
            max_length=64
        ),
        FieldSchema(
            name="embedding",
            dtype=DataType.FLOAT_VECTOR,
            dim=384   # MiniLM dimension
        ),
        FieldSchema(
            name="text",
            dtype=DataType.VARCHAR,
            max_length=2048
        )
    ]

    schema = CollectionSchema(
        fields=fields,
        description="RAG document chunks"
    )

    collection = Collection(
        name=COLLECTION_NAME,
        schema=schema
    )

    collection.create_index(
        field_name="embedding",
        index_params={
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",
            "params": {"nlist": 128}
        }
    )

    collection.load()
    print("Collection created & loaded")
