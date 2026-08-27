import hmac
from typing import Annotated, Optional
from fastapi import HTTPException, Header
from app.config.settings import settings

def validate_api_key(x_api_key: Annotated[Optional[str], Header()] = None):
    """
    Validate API key from request header
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key is required. Please provide 'X-API-Key' header."
        )

    # Constant-time comparison to avoid leaking key material via timing
    if not hmac.compare_digest(x_api_key.encode("utf-8"), settings.API_KEY.encode("utf-8")):
        raise HTTPException(
            status_code=403,
            detail="Invalid API key. Access denied."
        )

    return x_api_key
