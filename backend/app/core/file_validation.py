"""
File Validation Service
Validates uploaded files using MIME type detection
"""
import os
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Try to use python-magic, fallback to extension-based detection
try:
    import magic
    MIME_DETECTION = "magic"
except ImportError:
    MIME_DETECTION = "extension"
    logger.warning("python-magic not installed, using extension-based detection")


# Allowed MIME types for resumes
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/msword",  # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
}

# Allowed extensions
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


class FileValidationError(Exception):
    """File validation failed"""
    pass


def validate_file(file_content: bytes, filename: str, max_size: int = MAX_FILE_SIZE) -> Tuple[bool, Optional[str]]:
    """
    Validate file type and size
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    # Check file size
    if len(file_content) > max_size:
        return False, f"File too large. Maximum size is {max_size // (1024*1024)}MB"
    
    # Check extension
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Invalid file extension '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Detect MIME type
    mime_type = detect_mime_type(file_content, filename)
    
    if mime_type not in ALLOWED_MIME_TYPES:
        return False, f"Invalid file type '{mime_type}'. Allowed: {', '.join(ALLOWED_MIME_TYPES)}"
    
    return True, None


def detect_mime_type(file_content: bytes, filename: str) -> str:
    """Detect MIME type of file"""
    
    if MIME_DETECTION == "magic":
        try:
            # Check file header for PDF
            if file_content[:4] == b'%PDF':
                return "application/pdf"
            
            # Check for DOC/DOCX (ZIP-based)
            if file_content[:2] == b'PK':
                # Could be DOCX or other ZIP-based format
                if filename.lower().endswith('.docx'):
                    return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                return "application/zip"
            
            # Use magic for other types
            mime = magic.from_buffer(file_content[:2048], mime=True)
            return mime
            
        except Exception as e:
            logger.warning(f"MIME detection failed: {e}")
    
    # Fallback to extension-based detection
    ext = os.path.splitext(filename)[1].lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    return mime_map.get(ext, "application/octet-stream")


def is_safe_filename(filename: str) -> bool:
    """Check if filename is safe (no path traversal)"""
    # Remove any path components
    safe_name = os.path.basename(filename)
    
    # Check for dangerous characters
    dangerous_chars = ['/', '\\', '..', '\x00']
    for char in dangerous_chars:
        if char in safe_name:
            return False
    
    return bool(safe_name and len(safe_name) <= 255)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Get only the basename
    safe_name = os.path.basename(filename)
    
    # Replace dangerous characters
    safe_name = safe_name.replace('..', '_')
    safe_name = safe_name.replace('/', '_').replace('\\', '_')
    
    # Limit length
    if len(safe_name) > 200:
        ext = os.path.splitext(safe_name)[1]
        safe_name = safe_name[:200 - len(ext)] + ext
    
    return safe_name