import logging
import io
import tempfile
import os
from typing import Union, Tuple, Dict, Any, List
from docling.document_converter import DocumentConverter

logger = logging.getLogger(__name__)

def extract_text_and_tables_from_pdf(source: Union[str, bytes]) -> Tuple[Dict[int, str], List[Dict[str, Any]]]:
    """
    Extracts content using IBM Docling.
    
    This replaces the old manual extraction logic.
    Docling automatically detects tables, reading order, and headers.
    
    Returns: 
      - pages_text: Dict[page_num, markdown_content] (We typically return just {1: full_markdown} for simplicity, or split by page if possible)
      - tables: Empty list (because Docling embeds tables directly into the Markdown! we rely on Markdown structure now)
    """
    try:
        # Initialize converter
        # improved logic: Docling can handle bytesstreams using 'DocumentStream'
        # but for now, saving to temp file is the most robust way across versions
        
        converter = DocumentConverter()
        result = None
        
        if isinstance(source, bytes):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(source)
                tmp_path = tmp.name
            
            try:
                logger.info(f"Processing PDF from temp file: {tmp_path}")
                result = converter.convert(tmp_path)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        else:
             logger.info(f"Processing PDF from path: {source}")
             result = converter.convert(source)

        if not result:
            raise ValueError("Docling failed to convert document")
            
        # Serialize to Markdown
        # This string contains everything: Headers (#), Tables (| | |), and Text.
        markdown_output = result.document.export_to_markdown()
        
        logger.info(f"✅ Docling extraction successful. Total Markdown length: {len(markdown_output)}")
        
        # We return the whole markdown as "Page 1" for now to fit the existing contract
        # The downstream chunker will handle the splitting.
        return {1: markdown_output}, [] 

    except Exception as e:
        logger.error(f"❌ Docling conversion failed: {e}", exc_info=True)
        return {}, []

def extract_tables_from_pdf(source: Union[str, bytes]) -> list[dict[str, Any]]:
    """Legacy compatibility: returns empty list as tables are now in markdown."""
    return []

