from sentence_transformers import SentenceTransformer
import numpy as np

# Lazy load model
_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def embed_text(text: str) -> list[float]:
    model = get_model()
    embedding = model.encode(text)
    return embedding.tolist()
