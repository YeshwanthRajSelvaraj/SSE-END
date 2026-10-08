"""
Availability Defense: Rate Limiting
"""
import time
from fastapi import HTTPException, status
from app.config import settings

# In-memory token bucket/sliding window for IPs
request_history = {}

def rate_limit_ip(ip_address: str):
    """
    Basic sliding window rate limiting.
    Raises 429 if too many requests from an IP.
    """
    now = time.time()
    
    if ip_address not in request_history:
        request_history[ip_address] = []
        
    # Clean old requests
    window_start = now - settings.RATE_LIMIT_WINDOW_SECONDS
    request_history[ip_address] = [t for t in request_history[ip_address] if t > window_start]
    
    if len(request_history[ip_address]) >= settings.RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
        
    request_history[ip_address].append(now)
