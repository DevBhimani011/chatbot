from app.rag.search import search_similar_chunks
from app.rag.llm import generate_answer
from app.rag.reranker import reranker
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.5  # Lower threshold for retrieval (let reranker decide)
RETRIEVAL_K = 15  # Retrieve more chunks for reranking
TOP_K_RERANKED = 5  # Final chunks for LLM context


def answer_question(question: str) -> dict:
    logger.info(f"📝 Processing question: {question}")
    
    # 1️⃣ Retrieve similar chunks with broader search
    logger.info(f"🔍 Searching for top {RETRIEVAL_K} similar chunks...")
    results = search_similar_chunks(question, limit=RETRIEVAL_K)

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

    # 2️⃣ Rerank Candidates
    filtered = [r for r in results if r["similarity"] >= SIMILARITY_THRESHOLD]
    
    if not filtered:
         # Fallback to Top N of original if threshold excluded all (unlikely with 0.3)
         filtered = results[:5] 

    logger.info(f"🔄 Reranking {len(filtered)} candidates...")
    reranked_chunks = reranker.rerank(question, filtered, top_k=TOP_K_RERANKED)
    
    # Log Reranker Results
    logger.info(f"\n{'='*80}")
    logger.info(f"🏆 TOP {len(reranked_chunks)} RERANKED CHUNKS:")
    logger.info(f"{'='*80}")
    for i, r in enumerate(reranked_chunks, 1):
         logger.info(f"Rank {i}: Score={r.get('rerank_score', 0):.4f} (Vector Sim={r['similarity']:.4f}) | {r['filename']}")
         logger.info(f"Snippet: {r['text'][:200]}...")
    logger.info(f"{'='*80}\n")
    
    # 3️⃣ Merge context
    context = "\n\n".join(
        f"- {r['text']}" for r in reranked_chunks
    )
    
    # Print summary of chunks going to LLM
    logger.info(f"\n{'='*80}")
    logger.info(f"📦 {len(reranked_chunks)} CHUNKS PASSED SIMILARITY THRESHOLD (>= {SIMILARITY_THRESHOLD}):")
    logger.info(f"{'='*80}")
    for i, r in enumerate(reranked_chunks, 1):
        logger.info(f"Chunk {i}: Similarity = {r['similarity']:.4f} | Source: {r['filename']}")
    logger.info(f"{'-'*80}")
    logger.info(f"Total Context: {len(context)} chars (~{len(context)//4} tokens)")
    logger.info(f"{'-'*80}")
    logger.info(f"📝 FULL CONTEXT SENT TO LLM:\n{context}")
    logger.info(f"{'='*80}\n")

    # 4️⃣ Generate answer using LLM
    # generate_answer now returns a generator if successful
    return generate_answer(context=context, question=question)
