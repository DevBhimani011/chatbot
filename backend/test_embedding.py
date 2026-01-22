from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

text = "How can I apply for admission?"
embedding = model.encode(text)

print(len(embedding))   # should be 384
print(embedding[:10])   # preview
