from app.db.session import get_connection
from app.rag.embeddings import embed_text

def embed_all_chunks():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, chunk_text
        FROM document_chunks
        WHERE embedding IS NULL
    """)

    rows = cur.fetchall()

    for chunk_id, chunk_text in rows:
        vector = embed_text(chunk_text)

        cur.execute(
            """
            UPDATE document_chunks
            SET embedding = %s
            WHERE id = %s
            """,
            (vector, chunk_id)
        )

    conn.commit()
    cur.close()
    conn.close()

    print(f"Embedded {len(rows)} chunks")
    
if __name__ == "__main__":
    embed_all_chunks()

