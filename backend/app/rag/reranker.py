from typing import List, Dict, Any
import logging
from sentence_transformers import CrossEncoder
import torch

logger = logging.getLogger(__name__)

class Reranker:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Reranker, cls).__new__(cls)
            try:
                cls._instance._initialize()
            except Exception as e:
                logger.error(f"Error initializing Reranker: {e}")
                cls._instance._model = None
        return cls._instance

    def _initialize(self):
        """Initialize the CrossEncoder model."""
        model_name = "BAAI/bge-reranker-base"
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"🔄 Loading Reranker model: {model_name} on {device}...")
        try:
            self._model = CrossEncoder(model_name, device=device)
            logger.info("✅ Reranker model loaded successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to load Reranker model: {e}")
            self._model = None

    def rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Rerank a list of chunks based on their relevance to the query.
        
        Args:
            query: The user's question.
            chunks: List of chunk dictionaries (must contain 'text' key).
            top_k: Number of top chunks to return.
            
        Returns:
            List of reranked chunks with updated 'similarity' scores (from reranker).
        """
        if not self._model or not chunks:
            if not self._model:
                logger.warning("⚠️ Reranker model not loaded. Returning original chunks.")
            return chunks[:top_k]

        # Prepare pairs for CrossEncoder: [[query, doc1], [query, doc2], ...]
        pairs = [[query, chunk.get("text", "")] for chunk in chunks]

        try:
            # Predict scores
            scores = self._model.predict(pairs)
            
            # Update chunks with new scores
            for i, chunk in enumerate(chunks):
                # Normalize score if needed, but CrossEncoder scores are typically logits
                # Using the raw score is fine for ranking
                chunk["rerank_score"] = float(scores[i])
                # We can either overwrite 'similarity' or keep it. 
                # Let's keep 'similarity' as vector score and add 'rerank_score'.
            
            # Sort by rerank_score descending
            reranked_chunks = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
            
            return reranked_chunks[:top_k]

        except Exception as e:
            logger.error(f"❌ Error during reranking: {e}")
            # Fallback to original order
            return chunks[:top_k]

# Global instance
reranker = Reranker()
