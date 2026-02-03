"""
Check what's in Milvus and optionally clean everything.
"""

import os
from pymilvus import connections, utility, Collection

# Configuration
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))
COLLECTION_NAME = "document_chunks"

def check_milvus():
    print("🔍 Connecting to Milvus...")
    connections.connect(
        alias="default",
        host=MILVUS_HOST,
        port=MILVUS_PORT
    )
    
    print(f"\n📋 All collections in Milvus:")
    collections = utility.list_collections()
    for col in collections:
        print(f"  - {col}")
    
    if COLLECTION_NAME in collections:
        collection = Collection(COLLECTION_NAME)
        collection.load()
        
        count = collection.num_entities
        print(f"\n📊 Collection '{COLLECTION_NAME}' has {count} entities")
        
        # Sample some data
        print(f"\n📄 Sampling first 3 chunks:")
        results = collection.query(
            expr="id != ''",
            output_fields=["chunk_text", "filename", "page_number", "table_index", "row_index"],
            limit=3
        )
        
        for i, r in enumerate(results, 1):
            print(f"\n--- Sample {i} ---")
            print(f"Filename: {r.get('filename')}")
            print(f"Page: {r.get('page_number')} | Table: {r.get('table_index')} | Row: {r.get('row_index')}")
            text = r.get('chunk_text', '')
            print(f"Text (first 200 chars): {text[:200]}...")
            if text.startswith("TABLE_ROW"):
                print("✅ This is NEW format (structured table)")
            else:
                print("❌ This is OLD format (unstructured)")
    else:
        print(f"\n⚠️ Collection '{COLLECTION_NAME}' not found!")
    
    print("\n" + "="*80)
    response = input("Do you want to DELETE ALL DATA and recreate collection? (yes/no): ")
    
    if response.lower() == 'yes':
        print("\n🗑️ Dropping all collections...")
        for col in utility.list_collections():
            utility.drop_collection(col)
            print(f"  Dropped: {col}")
        
        print("\n✨ All data cleared! Now re-upload your PDFs through the API.")
        print("   The backend will auto-create the collection on first upload.")
    else:
        print("\n👍 No changes made.")

if __name__ == "__main__":
    check_milvus()
