import io
from typing import Union, Any, Tuple
import logging
import pdfplumber
from pdf2image import convert_from_bytes, convert_from_path
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)


def extract_text_and_tables_from_pdf(source: Union[str, bytes]) -> Tuple[dict[int, str], list[dict[str, Any]]]:
    """Extract both text and tables from PDF in a single pass using pdfplumber.
    This prevents duplication by filtering out text from table regions.
    
    Returns:
        Tuple of (pages_text_dict, tables_list)
    """
    try:
        if isinstance(source, bytes):
            pdf = pdfplumber.open(io.BytesIO(source))
        else:
            pdf = pdfplumber.open(source)
        
        pages_text = {}
        tables = []
        
        for page_number, page in enumerate(pdf.pages, start=1):
            # Extract tables first
            page_tables = page.extract_tables()
            
            if page_tables:
                # Store tables
                for table_index, table_rows in enumerate(page_tables, start=1):
                    if table_rows:
                        tables.append({
                            "page_number": page_number,
                            "table_index": table_index,
                            "rows": table_rows,
                        })
                
                # For pages with tables, extract text OUTSIDE table regions
                table_bboxes = page.find_tables()
                
                if table_bboxes:
                    # Filter out characters that overlap with table regions
                    filtered_page = page.filter(lambda obj: (
                        obj['object_type'] == 'char' and
                        not any(
                            _char_in_bbox(obj, table.bbox) 
                            for table in table_bboxes
                        )
                    ))
                    text = filtered_page.extract_text() if filtered_page else None
                else:
                    # No table bboxes found, skip text (table detection worked but no bbox)
                    text = None
            else:
                # No tables, extract all text
                text = page.extract_text()
            
            if text and text.strip():
                pages_text[page_number] = text.strip()
        
        pdf.close()
        logger.info(f"📄 Extracted text from {len(pages_text)} pages")
        logger.info(f"📊 Extracted {len(tables)} tables")
        
        # If no text was extracted, try OCR on scanned images
        if not pages_text and not tables:
            logger.info("⚠️ No text found with pdfplumber, attempting OCR...")
            pages_text, ocr_tables = _extract_with_ocr(source)
            if ocr_tables:
                tables.extend(ocr_tables)
        
        return pages_text, tables
        
    except Exception as e:
        logger.error(f"Error extracting text and tables: {e}")
        return {}, []


def _char_in_bbox(char, bbox):
    """Check if a character overlaps with a table bounding box."""
    x0, top, x1, bottom = bbox
    return (
        char['x0'] < x1 and  # char left < bbox right
        char['x1'] > x0 and  # char right > bbox left
        char['top'] < bottom and  # char top < bbox bottom
        char['bottom'] > top  # char bottom > bbox top
    )


def _extract_with_ocr(source: Union[str, bytes]) -> Tuple[dict[int, str], list[dict[str, Any]]]:
    """Extract text from scanned PDF using OCR."""
    try:
        # Convert PDF to images
        if isinstance(source, bytes):
            images = convert_from_bytes(source, dpi=300)
        else:
            images = convert_from_path(source, dpi=300)
        
        logger.info(f"🖼️ Converted PDF to {len(images)} images for OCR")
        
        pages_text = {}
        for page_number, image in enumerate(images, start=1):
            # Perform OCR on each page
            text = pytesseract.image_to_string(image, lang='eng')
            if text and text.strip():
                pages_text[page_number] = text.strip()
                logger.info(f"✅ OCR extracted {len(text)} chars from page {page_number}")
        
        logger.info(f"📄 OCR extracted text from {len(pages_text)} pages")
        return pages_text, []  # OCR doesn't extract tables separately
        
    except Exception as e:
        logger.error(f"❌ OCR extraction failed: {e}")
        return {}, []


def extract_tables_from_pdf(source: Union[str, bytes]) -> list[dict[str, Any]]:
    """Extract tables from PDF using pdfplumber.
    
    Returns a list of tables with page/table indexes and raw 2D rows.
    """
    try:
        # Open PDF with pdfplumber
        if isinstance(source, bytes):
            pdf = pdfplumber.open(io.BytesIO(source))
        else:
            pdf = pdfplumber.open(source)
        
        tables = []
        
        for page_number, page in enumerate(pdf.pages, start=1):
            page_tables = page.extract_tables()
            
            if page_tables:
                for table_index, table_rows in enumerate(page_tables, start=1):
                    if table_rows:
                        tables.append({
                            "page_number": page_number,
                            "table_index": table_index,
                            "rows": table_rows,
                        })
        
        pdf.close()
        logger.info(f"📊 Extracted {len(tables)} tables using pdfplumber")
        return tables
        
    except Exception as e:
        logger.error(f"Error extracting tables with pdfplumber: {e}")
        return []
