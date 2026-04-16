"""
Rate limiting and throttling utilities.
"""
import time
from functools import wraps
from fastapi import HTTPException
from typing import Dict, Tuple

# In-memory rate limiter (use Redis in production)
rate_limit_store: Dict[str, list] = {}


def rate_limit(max_calls: int, time_window: int = 60):
    """
    Rate limiting decorator.
    Args:
        max_calls: Maximum number of calls allowed
        time_window: Time window in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get identifier from request if available
            request = next((arg for arg in args if hasattr(arg, 'client')), None)
            if request:
                client_id = f"{request.client.host}:{request.client.port}" if request.client else "unknown"
            else:
                client_id = "unknown"
            
            now = time.time()
            
            # Initialize or clean old entries
            if client_id not in rate_limit_store:
                rate_limit_store[client_id] = []
            
            # Remove old entries outside time window
            rate_limit_store[client_id] = [
                timestamp for timestamp in rate_limit_store[client_id]
                if now - timestamp < time_window
            ]
            
            # Check limit
            if len(rate_limit_store[client_id]) >= max_calls:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Max {max_calls} requests per {time_window}s"
                )
            
            # Add current request
            rate_limit_store[client_id].append(now)
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
