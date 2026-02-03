from sentence_transformers import SentenceTransformer
import numpy as np

# Lazy load model
_model = None

def get_model():
    global _model
    if _model is None:
        # Using e5-large-v2: State-of-the-art retrieval model
        # 1024 dimensions, trained on billions of text pairs for Q&A
        # Requires instruction prefixes: "query:" for queries, "passage:" for documents
        _model = SentenceTransformer("intfloat/e5-large-v2")
    return _model

def embed_text(text: str) -> list[float]:
    """Embed document text with passage instruction prefix for e5 model."""
    model = get_model()
    # E5 requires "passage:" prefix for document embeddings
    text_with_instruction = f"passage: {text}"
    embedding = model.encode(text_with_instruction)
    return embedding.tolist()


def embed_query(query: str) -> list[float]:
    """Embed query with query instruction prefix for e5 model.
    
    E5 is trained to understand asymmetric search:
    - Queries get "query:" prefix
    - Documents get "passage:" prefix
    """
    model = get_model()
    # E5 requires "query:" prefix for query embeddings
    query_with_instruction = f"query: {query}"
    embedding = model.encode(query_with_instruction)
    return embedding.tolist()
