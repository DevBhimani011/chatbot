import re
from typing import List

CHUNK_SIZE = 400
CHUNK_OVERLAP = 80


def clean_text(text: str) -> str:
    # Normalize whitespace but keep newlines
    # 1. Replace tabs with spaces
    text = text.replace('\t', ' ')
    # 2. Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    # 3. Replace multiple newlines with max 2 newlines
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()


def split_into_sentences(text: str) -> List[str]:
    # Split by punctuation OR newlines (good for tables)
    # Keep the delimiters
    parts = re.split(r'(?<=[.!?])\s+|\n+', text)
    return [p.strip() for p in parts if p.strip()]


def chunk_text(text: str) -> List[str]:
    text = clean_text(text)
    sentences = split_into_sentences(text)

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= CHUNK_SIZE:
            current_chunk += " " + sentence
        else:
            chunks.append(current_chunk.strip())

            # overlap from previous chunk
            overlap = current_chunk[-CHUNK_OVERLAP:]
            current_chunk = overlap + " " + sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
