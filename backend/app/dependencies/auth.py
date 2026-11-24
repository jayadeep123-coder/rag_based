"""
Authentication dependency for securing FastAPI endpoints with Supabase Auth JWT.
"""

from typing import Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.supabase import verify_supabase_token

security = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Extracts the Bearer token from the Authorization header, validates it against
    Supabase Auth, and returns the authenticated user object.
    
    Raises 401 Unauthorized if the token is invalid, expired, or malformed.
    Never relies on client-provided user IDs.
    """
    token = credentials.credentials
    user = verify_supabase_token(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

