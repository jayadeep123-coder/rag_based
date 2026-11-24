"""
FastAPI router for RAG Q&A chat endpoint.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.config import settings
from app.core.supabase import get_supabase_client
from app.dependencies.auth import get_current_user
from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag import execute_rag_query

logger = logging.getLogger("chat")

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat_with_document(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Submits a user question for a selected document with abuse limits:
    - Max question length (default 1000 characters)
    - Max daily questions per user (default 50 questions/day)
    Retrieves top chunks from pgvector, prompts Gemini with strict grounding,
    returns the grounded answer, parsed citations, and found status.
    """
    # 1. Enforce max question length
    if len(request.question) > settings.MAX_QUESTION_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question exceeds maximum allowed length of {settings.MAX_QUESTION_LENGTH} characters (got {len(request.question)})."
        )

    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database service not configured."
        )

    # 2. Enforce daily question limit per user via query_logs
    try:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        daily_res = (
            supabase.table("query_logs")
            .select("id", count="exact")
            .eq("user_id", current_user["id"])
            .gte("created_at", today_start)
            .execute()
        )
        daily_count = daily_res.count if daily_res.count is not None else 0
        if daily_count >= settings.MAX_QUESTIONS_PER_USER_PER_DAY:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily question limit reached ({settings.MAX_QUESTIONS_PER_USER_PER_DAY} questions per day). Please try again tomorrow."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Could not check daily question count: {e}")

    try:
        response = execute_rag_query(
            document_id=request.document_id,
            question=request.question,
            user_id=current_user["id"]
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        err_msg = str(e)
        if "quota" in err_msg.lower() or "429" in err_msg.lower() or "resource_exhausted" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI service is currently busy or quota is exhausted. Please try again in a few moments."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat query: {err_msg}"
        )

