import requests
import os
from app.core.config import settings

# Use environment variable for Docker, fallback to localhost for local dev
OLLAMA_URL = settings.OLLAMA_URL
MODEL_NAME = "phi3"  # or mistral

def generate_answer(context: str, question: str) -> str:
    prompt = f"""
You are an assistant that answers questions ONLY using the provided context.

Rules:
- If the answer is not fully present in the context, say: "No answer found in the document."
- Do NOT use outside knowledge.
- Summarize when the question asks for a list or overview.

Context:
{context}

Question:
{question}

Answer:
""".strip()

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0
            }
        },
        timeout=300
    )

    response.raise_for_status()
    data = response.json()
    
    return {
        "answer": data.get("response", "").strip(),
        "prompt_tokens": data.get("prompt_eval_count", 0),
        "response_tokens": data.get("eval_count", 0),
        "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
    }
