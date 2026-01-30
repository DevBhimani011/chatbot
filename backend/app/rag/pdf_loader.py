import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from typing import Union, Any

import pdfplumber

def extract_text_from_pdf(source: Union[str, bytes]) -> str:
    if isinstance(source, bytes):
        doc = fitz.open(stream=source, filetype="pdf")
    else:
        doc = fitz.open(source)
        
    text = []

    for page in doc:
        page_text = page.get_text()
        
        # If the page has very little text, attempt OCR
        if not page_text.strip():
            try:
                # Zoom x2 for better OCR accuracy
                matrix = fitz.Matrix(2, 2)
                pix = page.get_pixmap(matrix=matrix)
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                # Using pytesseract to extract text from the image
                ocr_text = pytesseract.image_to_string(image)
                if ocr_text.strip():
                    page_text = ocr_text
            except Exception as e:
                print(f"OCR failed for page {page.number}: {e}")

        if page_text.strip():
            text.append(page_text)

    return "\n".join(text)


def extract_tables_from_pdf(source: Union[str, bytes]) -> list[dict[str, Any]]:
    """Extract tables from a PDF using pdfplumber.

    Returns a list of tables with page/table indexes and raw 2D rows.
    Note: This works best for digital PDFs (selectable text). Scanned PDFs
    typically need a dedicated OCR+layout pipeline for accurate table structure.
    """
    if isinstance(source, bytes):
        pdf_file: Any = io.BytesIO(source)
    else:
        pdf_file = source

    tables: list[dict[str, Any]] = []
    with pdfplumber.open(pdf_file) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            try:
                extracted = page.extract_tables() or []
            except Exception:
                extracted = []

            for table_index, rows in enumerate(extracted, start=1):
                if not rows:
                    continue
                # Normalize cells to strings
                normalized_rows: list[list[str]] = []
                for row in rows:
                    if row is None:
                        continue
                    normalized_rows.append([
                        (cell or "").strip() if isinstance(cell, str) else (str(cell).strip() if cell is not None else "")
                        for cell in row
                    ])

                if normalized_rows:
                    tables.append({
                        "page_number": page_index,
                        "table_index": table_index,
                        "rows": normalized_rows,
                    })

    return tables
