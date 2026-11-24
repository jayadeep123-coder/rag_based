"""
Configuration module for AI Mentor Backend.
Reads environment variables with validation and type casting via Pydantic Settings.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Google Gemini Configuration (must come from environment variables)
    GEMINI_API_KEY: str = ""
    GEMINI_EMBED_MODEL: str = ""
    GEMINI_CHAT_MODEL: str = ""
    EMBED_DIM: int = 768

    # RAG Tuning Parameters
    SIMILARITY_THRESHOLD: float = 0.45
    TOP_K: int = 6

    # Chunker Parameters (configurable constants)
    CHUNK_SIZE_TOKENS: int = 800
    CHUNK_OVERLAP_TOKENS: int = 120  # ~15% of 800 tokens

    # Abuse Limits (Configurable via Environment Variables)
    MAX_PDF_SIZE_MB: int = 10
    MAX_DOCS_PER_USER: int = 5
    MAX_QUESTIONS_PER_USER_PER_DAY: int = 50
    MAX_QUESTION_LENGTH: int = 1000

    # Server Configuration
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:4173,http://127.0.0.1:4173"
    ENVIRONMENT: str = "development"
    PORT: int = 8000

    @property
    def cors_origins(self) -> List[str]:
        """Parse comma-separated allowed origins into a list for FastAPI CORS."""
        return [
            origin.strip().rstrip("/")
            for origin in self.ALLOWED_ORIGINS.split(",")
            if origin.strip() and origin.strip() != "*"
        ]

    model_config = SettingsConfigDict(
        env_file=("backend/.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

