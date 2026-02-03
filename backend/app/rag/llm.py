import requests
import os
import logging
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Groq API configuration
GROK_API_KEY = settings.GROK_API_KEY
GROK_API_URL = settings.GROK_API_URL
GROK_MODEL = settings.GROK_MODEL

def generate_answer(context: str, question: str) -> dict:
    """Generate answer using Groq API."""
    
    if not GROK_API_KEY:
        logger.error("❌ GROK_API_KEY not set in environment variables")
        return {
            "answer": "Error: Groq API key not configured.",
            "prompt_tokens": 0,
            "response_tokens": 0,
            "total_tokens": 0
        }
    
    # Build messages for chat completion
    system_message = """You are a helpful assistant that extracts specific information from documents.

Instructions:
- Answer the question using ONLY information from the context below
- Extract the exact value requested (dates, names, numbers, etc.)
- If the information is in a table format, look for the relevant row and column
- Be concise and direct - provide just the answer
- If you truly cannot find the answer in the context, say: "No answer found in the document."""
    
    user_message = f"""Context:
{context}

Question:
{question}

Answer:"""
    
    # Log the prompt
    logger.info("\n" + "=" * 80)
    logger.info("📤 PROMPT SENT TO GROQ:")
    logger.info("=" * 80)
    logger.info(f"System: {system_message}")
    logger.info(f"User: {user_message}")
    logger.info("=" * 80)
    logger.info(f"📊 Prompt length: {len(system_message) + len(user_message)} chars")
    logger.info("=" * 80 + "\n")
    
    try:
        # Log API details (without exposing full key)
        logger.info(f"🔑 Using Groq API key: {GROK_API_KEY[:10]}...{GROK_API_KEY[-4:]}")
        logger.info(f"🌐 API URL: {GROK_API_URL}")
        logger.info(f"🤖 Model: {GROK_MODEL}")
        
        response = requests.post(
            GROK_API_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROK_API_KEY}"
            },
            json={
                "model": GROK_MODEL,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0,
                "max_tokens": 500,
                "stream": False
            },
            timeout=30  # Groq is very fast
        )
        
        # Log response details for debugging
        logger.info(f"📡 Response status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"❌ Response body: {response.text}")
        
        response.raise_for_status()
        data = response.json()
        
        # Extract answer from Grok response
        answer = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        usage = data.get("usage", {})
        
        # Log the response
        logger.info("\n" + "=" * 80)
        logger.info("📥 RESPONSE FROM GROQ:")
        logger.info("=" * 80)
        logger.info(answer)
        logger.info("=" * 80)
        logger.info(f"📊 Usage: {usage.get('prompt_tokens', 0)} prompt tokens, {usage.get('completion_tokens', 0)} response tokens")
        logger.info("=" * 80 + "\n")
        
        return {
            "answer": answer,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "response_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0)
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Groq API error: {str(e)}")
        return {
            "answer": f"Error calling Groq API: {str(e)}",
            "prompt_tokens": 0,
            "response_tokens": 0,
            "total_tokens": 0
        }
