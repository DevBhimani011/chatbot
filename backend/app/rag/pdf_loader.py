import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from typing import Union

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
