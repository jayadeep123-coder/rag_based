"""
Supabase client helper and token verification service.
"""

from functools import lru_cache
from typing import Optional, Dict, Any
from supabase import create_client, Client
from app.core.config import settings


@lru_cache()
def get_supabase_client() -> Optional[Client]:
    """
    Returns a cached Supabase client initialized with the Service Role key.
    Enables server-side database operations and storage management.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        return None
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def verify_supabase_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifies a Supabase JWT access token using the Supabase Auth API.
    Returns user details dictionary if valid, None otherwise.
    """
    client = get_supabase_client()
    if not client:
        raise RuntimeError("Supabase client is not configured. Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")

    try:
        user_response = client.auth.get_user(token)
        if user_response and user_response.user:
            return {
                "id": str(user_response.user.id),
                "email": user_response.user.email,
                "role": user_response.user.role,
            }
        return None
    except Exception as e:
        # Token invalid, expired, or communication failure
        return None

