from app.rag.search import search_similar_chunks
from app.rag.llm import generate_answer
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.7  # Balanced threshold for quality matches
TOP_K = 3  # Focused retrieval for better performance


def answer_question(question: str) -> dict:
    logger.info(f"📝 Processing question: {question}")
    
    # 1️⃣ Retrieve similar chunks with broader search
    logger.info(f"🔍 Searching for top {TOP_K} similar chunks...")
    results = search_similar_chunks(question, limit=TOP_K)

    if not results:
        logger.warning("⚠️ No similar chunks found in vector database")
        return {
            "answer": "No answer found in the document.",
            "prompt_tokens": 0,
            "response_tokens": 0,
            "total_tokens": 0
        }

    # Log all retrieved chunks before filtering
    logger.info(f"\n{'='*80}")
    logger.info(f"📥 RETRIEVED {len(results)} CHUNKS FROM VECTOR DB:")
    logger.info(f"{'='*80}")
    for i, r in enumerate(results, 1):
        logger.info(f"\n--- Chunk {i} (Similarity: {r['similarity']:.4f}) ---")
        logger.info(f"Source: {r['filename']} | Page: {r.get('page_number', 0)} | Table: {r.get('table_index', 0)} | Row: {r.get('row_index', 0)}")
        logger.info(f"Content:\n{r['text'][:500]}..." if len(r['text']) > 500 else f"Content:\n{r['text']}")
    logger.info(f"{'='*80}\n")

    # 2️⃣ Filter by similarity threshold and take top chunks
    filtered = [r for r in results if r["similarity"] >= SIMILARITY_THRESHOLD]
    
    # Take top 10 chunks for LLM context (increased from 5)
    filtered = filtered[:5]

    if not filtered:
        logger.warning(f"⚠️ No chunks meet minimum similarity threshold of {SIMILARITY_THRESHOLD}")
        logger.warning(f"Best similarity found: {max(r['similarity'] for r in results):.4f}")
        return {
            "answer": "No answer found in the document.",
            "prompt_tokens": 0,
            "response_tokens": 0,
            "total_tokens": 0
        }

    # 3️⃣ Merge context
    context = "\n\n".join(
        f"- {r['text']}" for r in filtered
    )
    
    # Print summary of chunks going to LLM
    logger.info(f"\n{'='*80}")
    logger.info(f"📦 {len(filtered)} CHUNKS PASSED SIMILARITY THRESHOLD (>= {SIMILARITY_THRESHOLD}):")
    logger.info(f"{'='*80}")
    for i, r in enumerate(filtered, 1):
        logger.info(f"Chunk {i}: Similarity = {r['similarity']:.4f} | Source: {r['filename']}")
    logger.info(f"{'-'*80}")
    logger.info(f"Total Context: {len(context)} chars (~{len(context)//4} tokens)")
    logger.info(f"{'-'*80}")
    logger.info(f"📝 FULL CONTEXT SENT TO LLM:\n{context}")
    logger.info(f"{'='*80}\n")

    # 4️⃣ Generate answer using LLM
    # generate_answer now returns a generator if successful
    return generate_answer(context=context, question=question)
