from cryptography.fernet import Fernet
from app.core.config import settings

_fernet = None


def get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(settings.ENCRYPTION_KEY.encode())
    return _fernet


def encrypt(value: str) -> str:
    """Encrypt a PII string value using Fernet symmetric encryption."""
    if not value:
        return value
    return get_fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    """Decrypt a PII string value using Fernet symmetric encryption."""
    if not value:
        return value
    return get_fernet().decrypt(value.encode()).decode()
