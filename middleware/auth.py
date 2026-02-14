"""
Auth middleware — Firebase token verification dependencies.
Re-exports get_current_user from the auth router for use across all routers.
Also provides get_optional_user for endpoints that work with or without auth.
"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from config.firebase_init import verify_firebase_token
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)
optional_security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Require valid Firebase token. Raises 401 if invalid."""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    try:
        decoded = verify_firebase_token(credentials.credentials)
        return decoded
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
) -> Optional[dict]:
    """Optionally verify Firebase token. Returns None if no token provided."""
    if not credentials:
        return None
    try:
        return verify_firebase_token(credentials.credentials)
    except Exception:
        return None
