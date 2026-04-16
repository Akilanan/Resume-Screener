import pdfplumber
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    try:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if not text.strip():
            raise ValueError("Empty PDF — no text extracted")
        return text
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""
