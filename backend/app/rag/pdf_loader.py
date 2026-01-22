import fitz  # PyMuPDF

def extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    text = []

    for page in doc:
        page_text = page.get_text()
        if page_text.strip():
            text.append(page_text)

    return "\n".join(text)
