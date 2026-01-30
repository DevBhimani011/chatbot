import re
from typing import List

from typing import Any

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


def table_rows_to_chunks(
    tables: list[dict[str, Any]],
    *,
    max_fields: int = 32,
) -> list[dict[str, Any]]:
    """Convert extracted pdf tables into row-level chunks.

    Each returned item contains `text` plus metadata fields:
    page_number, table_index, row_index.
    """
    results: list[dict[str, Any]] = []

    def _is_empty_row(row: list[str]) -> bool:
        return all((c or "").strip() == "" for c in row)

    for table in tables or []:
        rows: list[list[str]] = table.get("rows") or []
        if not rows:
            continue

        # Pick first non-empty row as header
        header_row: list[str] | None = None
        header_row_index: int | None = None
        for idx, row in enumerate(rows):
            if not _is_empty_row(row):
                header_row = [(c or "").strip() for c in row]
                header_row_index = idx
                break

        if header_row is None:
            continue

        base_headers = [h if h else f"Column {i+1}" for i, h in enumerate(header_row)]
        base_headers = base_headers[:max_fields]

        for absolute_row_index, row in enumerate(rows[(header_row_index + 1) :], start=1):
            if _is_empty_row(row):
                continue

            values = [(c or "").strip() for c in row][:max_fields]

            headers = list(base_headers)
            # Normalize lengths
            if len(values) < len(headers):
                values.extend([""] * (len(headers) - len(values)))
            elif len(values) > len(headers):
                extra_headers = [f"Column {i+1}" for i in range(len(headers), len(values))]
                headers = (headers + extra_headers)[:max_fields]
                values = values[: len(headers)]

            # Build a header-aware row representation (helps embeddings + LLM)
            fields = "; ".join(
                f"{headers[i]}: {values[i]}" for i in range(min(len(headers), len(values))) if headers[i]
            )
            header_line = " | ".join(headers)
            row_line = " | ".join(values)

            chunk_text = (
                "TABLE_ROW\n"
                f"Page: {table.get('page_number')}\n"
                f"Table: {table.get('table_index')}\n"
                f"Headers: {header_line}\n"
                f"Row: {row_line}\n"
                f"Fields: {fields}"
            ).strip()

            results.append({
                "text": chunk_text,
                "page_number": int(table.get("page_number") or 0),
                "table_index": int(table.get("table_index") or 0),
                "row_index": int(absolute_row_index),
            })

    return results
