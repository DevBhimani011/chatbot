from app.rag.chunking import chunk_text

text = """
Admission Process:
Step 1: Fill the form.
Step 2: Submit documents.

Fee Structure:
The tuition fee is 50000 per year.
"""

chunks = chunk_text(text)

for i, c in enumerate(chunks, 1):
    print(f"\n--- Chunk {i} ---")
    print(c)
    print("Length:", len(c))
