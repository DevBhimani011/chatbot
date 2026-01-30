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

SIMILARITY_THRESHOLD = 0.3
TOP_K = 5


def answer_question(question: str) -> dict:
    logger.info(f"📝 Processing question: {question}")
    
    # 1️⃣ Retrieve similar chunks
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

    # 2️⃣ Filter by similarity threshold
    filtered = [r for r in results if r["similarity"] >= SIMILARITY_THRESHOLD]

    if not filtered:
        logger.warning(f"⚠️ No chunks meet minimum similarity threshold of {SIMILARITY_THRESHOLD}")
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
    print(f"\n{'='*50}")
    print(f"📦 CHUNKS SENT TO LLM ({len(filtered)} chunks):")
    print(f"{'='*50}")
    for i, r in enumerate(filtered, 1):
        print(f"Chunk {i}: Similarity = {r['similarity']:.4f} | Source: {r['filename']}")
    print(f"{'-'*50}")
    print(f"Total Context: {len(context)} chars (~{len(context)//4} tokens)")
    print(f"{'='*50}\n")

    # 4️⃣ Generate answer using LLM
    response = generate_answer(context=context, question=question)
    
    return response
