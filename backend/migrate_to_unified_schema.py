"""
Migration script to transition from separate text/table collections to unified schema.

This script will:
1. Drop old collections (document_chunks and document_table_rows)
2. Create new unified collection (document_chunks)

WARNING: This will delete all existing data. Make sure to re-ingest your documents after running this.
"""

import os
from pymilvus import utility, connections, FieldSchema, CollectionSchema, DataType, Collection

# Configuration
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))
COLLECTION_NAME = "document_chunks"
DIMENSION = 384

def create_unified_collection():
    """Create unified collection directly without importing full app."""
    if utility.has_collection(COLLECTION_NAME):
        print(f"ℹ️  Collection {COLLECTION_NAME} already exists")
        return

    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
        FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=DIMENSION),
        FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=4000),
        FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=256),
        FieldSchema(name="page_number", dtype=DataType.INT64, default_value=0),
        FieldSchema(name="table_index", dtype=DataType.INT64, default_value=0),
        FieldSchema(name="row_index", dtype=DataType.INT64, default_value=0),
    ]

    schema = CollectionSchema(fields, description="Unified RAG document chunks")
    collection = Collection(COLLECTION_NAME, schema)

    collection.create_index(
        field_name="embedding",
        index_params={
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128},
        },
    )

    print("✨ Created unified collection successfully")

def migrate():
    print("🔄 Starting migration to unified schema...")
    
    # Connect to Milvus
    connections.connect(
        alias="default",
        host=MILVUS_HOST,
        port=MILVUS_PORT
    )
    
    # Drop old collections if they exist
    old_collections = ["document_chunks", "document_table_rows"]
    
    for collection_name in old_collections:
        if utility.has_collection(collection_name):
            print(f"🗑️  Dropping old collection: {collection_name}")
            utility.drop_collection(collection_name)
        else:
            print(f"ℹ️  Collection not found: {collection_name}")
    
    # Create new unified collection
    print("✨ Creating new unified collection...")
    create_unified_collection()
    
    print("✅ Migration complete!")
    print("\n⚠️  IMPORTANT: You need to re-ingest all your documents for them to appear in the new schema.")
    print("   Upload your PDFs again through the API to populate the new collection.")

if __name__ == "__main__":
    migrate()
