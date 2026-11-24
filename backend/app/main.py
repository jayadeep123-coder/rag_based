"""
FastAPI application entry point for AI Mentor API.
"""

import time
import uuid
import logging
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.supabase import get_supabase_client
from app.dependencies.auth import get_current_user
from app.models.schemas import HealthResponse, UserResponse
from app.routers import documents, chat

# Configure logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup check & stuck-document recovery:
    1. Validates configured models and API key.
    2. Recovers any documents left in 'processing' state older than 10 minutes.
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key or api_key.startswith("PASTE_"):
        raise RuntimeError(
            "Startup Check Failed: GEMINI_API_KEY is missing or unconfigured in backend/.env. "
            "Please configure a valid Gemini API key."
        )

    embed_model = settings.GEMINI_EMBED_MODEL.strip()
    if not embed_model:
        raise RuntimeError(
            "Startup Check Failed: GEMINI_EMBED_MODEL is missing or unconfigured in backend/.env. "
            "Model names must be set via environment variables."
        )

    chat_model = settings.GEMINI_CHAT_MODEL.strip()
    if not chat_model:
        raise RuntimeError(
            "Startup Check Failed: GEMINI_CHAT_MODEL is missing or unconfigured in backend/.env. "
            "Model names must be set via environment variables."
        )

    logger.info("=" * 60)
    logger.info("AI Mentor Backend Starting Up")
    logger.info(f"  Embedding Model: {embed_model} (dim={settings.EMBED_DIM})")
    logger.info(f"  Chat Model:      {chat_model}")
    logger.info(f"  Environment:     {settings.ENVIRONMENT}")
    logger.info("=" * 60)

    # 2. Stuck-document recovery on startup (e.g. following a dyno restart or sleep)
    try:
        supabase = get_supabase_client()
        if supabase:
            cutoff = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
            stuck_res = (
                supabase.table("documents")
                .select("id, filename")
                .eq("status", "processing")
                .lt("created_at", cutoff)
                .execute()
            )
            stuck_docs = stuck_res.data or []
            if stuck_docs:
                logger.warning(f"Found {len(stuck_docs)} interrupted processing document(s). Cleaning up...")
                for doc in stuck_docs:
                    doc_id = doc["id"]
                    supabase.table("chunks").delete().eq("document_id", doc_id).execute()
                    supabase.table("documents").update({
                        "status": "failed",
                        "error": "Processing was interrupted. Please re-upload or click Retry."
                    }).eq("id", doc_id).execute()
                logger.info(f"Stuck document recovery complete: {len(stuck_docs)} documents marked failed.")
    except Exception as e:
        logger.error(f"Error checking for stuck documents on startup: {e}")

    yield

    logger.info("AI Mentor Backend Shutting Down.")


# Request logging middleware: logs request id, method, path, status, and latency.
# Never logs authorization tokens, keys, passwords, or raw document content.
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = uuid.uuid4().hex[:8]
        start_time = time.perf_counter()
        response = await call_next(request)
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(f"[{req_id}] {request.method} {request.url.path} -> {response.status_code} ({latency_ms}ms)")
        response.headers["X-Request-ID"] = req_id
        return response


app = FastAPI(
    title="AI Mentor API",
    version="1.0.0",
    description="Backend API for PDF RAG with page-aware citations using Supabase & Google Gemini.",
    lifespan=lifespan
)

# Safe request logging
app.add_middleware(RequestLoggingMiddleware)

# Configure Cross-Origin Resource Sharing (CORS)
origins = settings.cors_origins
if not origins:
    origins = ["http://localhost:5173", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Register routers
app.include_router(documents.router)
app.include_router(chat.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"An unexpected server error occurred: {str(exc)}"}
    )


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint for deployment monitoring (Render/Kubernetes)
    and initial connectivity verification.
    """
    return HealthResponse(
        status="ok",
        environment=settings.ENVIRONMENT
    )


@app.get("/api/auth/me", response_model=UserResponse, tags=["Auth"])
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """
    Returns the authenticated user details extracted from the Supabase JWT.
    Validates end-to-end token verification.
    """
    return UserResponse(
        id=current_user["id"],
        email=current_user.get("email")
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
