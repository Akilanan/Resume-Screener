import pdfplumber
import logging
import os

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    try:
        logger.info(f"Starting extraction for: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"File does not exist: {file_path}")
            return ""
        
        file_size = os.path.getsize(file_path)
        logger.info(f"File size: {file_size} bytes")
        
        if file_size == 0:
            logger.error("File is empty")
            return ""
        
        with open(file_path, "rb") as f:
            header = f.read(4)
            logger.info(f"File header (hex): {header.hex()}")
        
        # Check if it's a valid PDF
        if header == b"%PDF":
            logger.info("Valid PDF detected, extracting text...")
            text = ""
            with pdfplumber.open(file_path) as pdf:
                logger.info(f"PDF pages: {len(pdf.pages)}")
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    logger.info(f"Page {i}: {len(page_text) if page_text else 0} chars")
                    if page_text:
                        text += page_text + "\n"
            
            if text.strip():
                logger.info(f"PDF text extracted: {len(text)} chars")
                return text
        
        # Not a valid PDF - try reading as plain text
        logger.info("Not a valid PDF, trying as plain text...")
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        
        if text.strip():
            logger.info(f"Text file read successfully: {len(text)} chars")
            return text
        
        logger.error("File appears empty")
        return ""
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return ""
