from fastapi import HTTPException, Header
from typing import Annotated
from app.config.settings import settings

def validate_api_key(x_api_key: Annotated[str, Header()]):
    """
    Validate API key from request header
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key is required. Please provide 'X-API-Key' header."
        )
    
    # Check if the provided key matches our API key
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key. Access denied."
        )
    
    return x_api_key 