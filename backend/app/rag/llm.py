import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
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
        timeout=120
    )

    response.raise_for_status()
    return response.json()["response"].strip()
