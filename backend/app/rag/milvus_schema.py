from pymilvus import (
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    utility,
)
from app.rag.milvus_client import connect_milvus

TEXT_COLLECTION_NAME = "document_chunks"
TABLE_ROWS_COLLECTION_NAME = "document_table_rows"
DIMENSION = 384  # all-MiniLM-L6-v2


def create_text_collection():
    connect_milvus()

    if utility.has_collection(TEXT_COLLECTION_NAME):
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
            max_length=2000,
        ),
        FieldSchema(
            name="filename",
            dtype=DataType.VARCHAR,
            max_length=256,
        ),
    ]

    schema = CollectionSchema(fields, description="RAG document chunks")
    collection = Collection(TEXT_COLLECTION_NAME, schema)

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


def create_table_rows_collection():
    connect_milvus()

    if utility.has_collection(TABLE_ROWS_COLLECTION_NAME):
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
            max_length=2000,
        ),
        FieldSchema(
            name="filename",
            dtype=DataType.VARCHAR,
            max_length=256,
        ),
        FieldSchema(
            name="page_number",
            dtype=DataType.INT64,
        ),
        FieldSchema(
            name="table_index",
            dtype=DataType.INT64,
        ),
        FieldSchema(
            name="row_index",
            dtype=DataType.INT64,
        ),
    ]

    schema = CollectionSchema(fields, description="RAG table rows (header-aware)")
    collection = Collection(TABLE_ROWS_COLLECTION_NAME, schema)

    collection.create_index(
        field_name="embedding",
        index_params={
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128},
        },
    )

    print("Milvus table rows collection created successfully")


def create_collection():
    # Backwards compatibility: create the text collection
    create_text_collection()


def create_all_collections():
    create_text_collection()
    create_table_rows_collection()


if __name__ == "__main__":
    create_all_collections()
