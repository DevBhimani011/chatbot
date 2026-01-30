import re

from app.rag.search import search_similar_chunks, query_table_rows_like
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


_DOB_QUESTION_RE = re.compile(r"(?:date\s+of\s+birth|dob)\s+of\s+(.+?)[\?\.\s]*$", re.IGNORECASE)


def _extract_dob_from_table_chunk(chunk_text: str) -> str | None:
    if not chunk_text:
        return None

    # 1) Prefer the explicit Fields line
    fields_idx = chunk_text.find("Fields:")
    if fields_idx != -1:
        fields_str = chunk_text[fields_idx + len("Fields:") :].strip()
        for part in [p.strip() for p in fields_str.split(";") if p.strip()]:
            if ":" not in part:
                continue
            key, value = part.split(":", 1)
            key_norm = key.strip().lower()
            value = value.strip()
            if ("date of birth" in key_norm) or (key_norm in {"dob"}) or ("birth" in key_norm):
                if value:
                    return value

    # 2) Fallback: locate DOB column by headers/row
    header_match = re.search(r"^Headers:\s*(.+)$", chunk_text, re.MULTILINE)
    row_match = re.search(r"^Row:\s*(.+)$", chunk_text, re.MULTILINE)
    if header_match and row_match:
        headers = [h.strip().lower() for h in header_match.group(1).split("|")]
        values = [v.strip() for v in row_match.group(1).split("|")]
        for idx, h in enumerate(headers):
            if "date of birth" in h or h == "dob":
                if 0 <= idx < len(values) and values[idx]:
                    return values[idx]

    return None


def answer_question(question: str) -> dict:
    logger.info(f"📝 Processing question: {question}")

    # High-precision table lookup for DOB questions (avoids embedding misses)
    match = _DOB_QUESTION_RE.search(question.strip())
    if match:
        person_name = match.group(1).strip()
        logger.info(f"🎯 DOB lookup detected for name: {person_name}")

        try:
            exact_rows = query_table_rows_like(person_name, limit=10)
        except Exception as e:
            logger.warning(f"⚠️ Exact table-row lookup failed: {e}")
            exact_rows = []

        for row in exact_rows:
            dob = _extract_dob_from_table_chunk(row.get("text") or "")
            if dob:
                return {
                    "answer": f"{person_name} was born on {dob}.",
                    "prompt_tokens": 0,
                    "response_tokens": 0,
                    "total_tokens": 0,
                }

        # If we found candidate rows but couldn't parse reliably, let the LLM decide
        if exact_rows:
            context = "\n\n".join(f"- {r['text']}" for r in exact_rows)
            return generate_answer(context=context, question=question)
    
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
