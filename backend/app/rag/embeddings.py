from sentence_transformers import SentenceTransformer
import numpy as np

# Load model once (VERY IMPORTANT)
model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text: str) -> list[float]:
    embedding = model.encode(text)
    return embedding.tolist()
