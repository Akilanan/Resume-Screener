from datetime import datetime, timedelta
from jose import JWTError, jwt, ExpiredSignatureError
from passlib.context import CryptContext
from app.core.config import settings
import random
import string
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    if not plain or not hashed:
        return False
    try:
        return pwd_context.verify(plain, hashed)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create a JWT access token"""
    try:
        payload = data.copy()
        
        # Set expiration - default 24 hours
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        payload.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        logger.info(f"Created access token for user: {data.get('sub', 'unknown')}, expires: {expire}")
        return token
        
    except Exception as e:
        logger.error(f"Failed to create access token: {e}")
        raise


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token (7 days)"""
    try:
        payload = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        
        payload.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        
    except Exception as e:
        logger.error(f"Failed to create refresh token: {e}")
        raise


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token
    
    Raises:
        ExpiredSignatureError: Token has expired
        JWTError: Token is invalid
    """
    try:
        if not token or not isinstance(token, str):
            raise JWTError("Token must be a non-empty string")
        
        # Check token format
        if token.count('.') != 2:
            raise JWTError("Invalid token format")
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        
        # Validate required fields
        if "exp" not in payload:
            raise JWTError("Token missing expiration")
        if "type" not in payload:
            raise JWTError("Token missing type")
            
        return payload
        
    except ExpiredSignatureError:
        logger.warning("Token has expired")
        raise
    except JWTError as e:
        logger.warning(f"JWT validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected token decode error: {e}")
        raise JWTError(f"Token decode failed: {str(e)}")


def verify_token_type(token: str, expected_type: str) -> dict:
    """
    Verify token and check its type
    
    Args:
        token: The JWT token
        expected_type: 'access' or 'refresh'
    
    Returns:
        The decoded payload
        
    Raises:
        JWTError: If token type doesn't match
    """
    payload = decode_token(token)
    token_type = payload.get("type")
    
    if token_type != expected_type:
        raise JWTError(f"Token type mismatch. Expected {expected_type}, got {token_type}")
    
    return payload


def get_token_expiry(token: str) -> datetime:
    """Get token expiration time"""
    payload = decode_token(token)
    exp = payload.get("exp")
    if exp:
        return datetime.fromtimestamp(exp)
    return None


def is_token_expired(token: str) -> bool:
    """Check if a token is expired (without raising exception)"""
    try:
        decode_token(token)
        return False
    except ExpiredSignatureError:
        return True
    except JWTError:
        return True


def generate_otp(length: int = 6) -> str:
    """Generate a secure random OTP"""
    return "".join(random.choices(string.digits, k=length))


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))
