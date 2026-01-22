from app.rag.search import search_similar_chunks
from app.rag.llm import generate_answer


SIMILARITY_THRESHOLD = 0.3
TOP_K = 5


def answer_question(question: str) -> str:
    # 1️⃣ Retrieve similar chunks
    results = search_similar_chunks(question, limit=TOP_K)

    if not results:
        return "No answer found in the document."

    # 2️⃣ Filter by similarity threshold
    filtered = [r for r in results if r["similarity"] >= SIMILARITY_THRESHOLD]

    if not filtered:
        return "No answer found in the document."

    # 3️⃣ Merge context
    context = "\n\n".join(
        f"- {r['text']}" for r in filtered
    )

    # 4️⃣ Generate answer using LLM
    return generate_answer(context=context, question=question)
