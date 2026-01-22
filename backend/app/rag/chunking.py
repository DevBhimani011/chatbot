import re
from typing import List

CHUNK_SIZE = 400
CHUNK_OVERLAP = 80


def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def split_into_sentences(text: str) -> List[str]:
    return re.split(r'(?<=[.!?])\s+', text)


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
