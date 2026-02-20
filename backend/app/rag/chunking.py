import re
from typing import List



CHUNK_SIZE = 800
CHUNK_OVERLAP = 160


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



def chunk_markdown(text: str, chunk_size: int = 1500, overlap: int = 200) -> List[str]:
    """
    Chunks Markdown text while respecting structure (Headers, Tables).
    
    Strategy:
    1.  Split by top-level headers (#, ##) to keep sections together.
    2.  If a section is too big, split by paragraphs/newlines but try to keep tables content together.
    3.  If a table is split, inject the last active Header to maintain context.
    """
    # Simple recursive splitting for now
    # In a full implementation, we'd build a tree of sections.
    
    # 1. Normalize
    text = text.strip()
    if not text:
        return []
        
    chunks = []
    
    # Split by double newline to get paragraphs/blocks
    blocks = re.split(r'\n\n+', text)
    
    current_chunk = []
    current_length = 0
    last_header = ""
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
            
        # Check if block is a header
        if block.startswith("#"):
             last_header = block.split('\n')[0] # Take the first line if multiple
             
        block_len = len(block)
        
        # If adding this block exceeds size
        if current_length + block_len > chunk_size and current_length > 0:
            # Finalize current chunk
            chunk_str = "\n\n".join(current_chunk)
            chunks.append(chunk_str)
            
            # Start new chunk
            # Inject context (Header) if appropriate
            current_chunk = []
            current_length = 0
            
            if last_header and not block.startswith("#"):
                 # Inject header if we are continuing a section
                 current_chunk.append(f"(Context: {last_header})")
                 current_length += len(current_chunk[0])
        
        current_chunk.append(block)
        current_length += block_len
        
    # Add remainder
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
        
    return chunks
