import re
from typing import List

from typing import Any

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


def table_rows_to_chunks(
    tables: list[dict[str, Any]],
    *,
    max_fields: int = 32,
) -> list[dict[str, Any]]:
    """Convert extracted pdf tables into row-level chunks.
    
    Each row is stored with its complete header information for better semantic search.
    Handles complex tables with merged cells and varying structures.
    """
    results: list[dict[str, Any]] = []

    def _is_empty_row(row: list[str]) -> bool:
        return all((c or "").strip() == "" for c in row)
    
    def _clean_value(val: str) -> str:
        """Clean and normalize cell values."""
        if not val:
            return ""
        # Remove excessive whitespace
        val = " ".join(val.split())
        return val.strip()

    for table in tables or []:
        rows: list[list[str]] = table.get("rows") or []
        if not rows:
            continue

        # Find the first non-empty row as header
        header_row: list[str] | None = None
        data_start_idx: int = 0
        
        for idx, row in enumerate(rows):
            if not _is_empty_row(row):
                header_row = [_clean_value(c or "") for c in row]
                data_start_idx = idx + 1
                break

        if header_row is None or data_start_idx >= len(rows):
            continue

        # Normalize header: assign default names to empty headers
        base_headers = [h if h else f"Column {i+1}" for i, h in enumerate(header_row)]
        base_headers = base_headers[:max_fields]

        # Process each data row
        for row_idx, row in enumerate(rows[data_start_idx:], start=1):
            if _is_empty_row(row):
                continue

            # Clean all cell values
            values = [_clean_value(c or "") for c in row][:max_fields]
            
            # Match header and value lengths
            headers = list(base_headers)
            if len(values) < len(headers):
                values.extend([""] * (len(headers) - len(values)))
            elif len(values) > len(headers):
                # Add generic headers for extra columns
                extra_headers = [f"Column {i+1}" for i in range(len(headers), len(values))]
                headers = (headers + extra_headers)[:max_fields]
                values = values[:len(headers)]

            # Build multiple representations for robust search
            
            # 1. Structured field list (key: value pairs)
            field_pairs = []
            for i in range(len(headers)):
                if headers[i] and values[i]:
                    field_pairs.append(f"{headers[i]}: {values[i]}")
            fields_text = "; ".join(field_pairs)
            
            # 2. Header and row as pipe-separated
            header_line = " | ".join(headers)
            row_line = " | ".join(values)
            
            # 3. Natural language context for better embeddings
            natural_sentences = []
            for i in range(len(headers)):
                if headers[i] and values[i]:
                    natural_sentences.append(f"The {headers[i]} is {values[i]}")
            natural_text = ". ".join(natural_sentences)
            
            # 4. Concatenate all values for text search
            all_values = " ".join([v for v in values if v])

            # Build final chunk with multiple formats
            chunk_text = (
                f"TABLE_ROW\n"
                f"Page: {table.get('page_number')}\n"
                f"Table: {table.get('table_index')}\n"
                f"Headers: {header_line}\n"
                f"Row: {row_line}\n"
                f"Fields: {fields_text}\n"
                f"Context: {natural_text}\n"
                f"Content: {all_values}"
            ).strip()

            results.append({
                "text": chunk_text,
                "page_number": int(table.get("page_number") or 0),
                "table_index": int(table.get("table_index") or 0),
                "row_index": row_idx,
            })

    return results
