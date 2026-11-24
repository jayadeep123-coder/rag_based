"""
Pydantic schemas for request and response serialization.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    environment: str = "development"


class UserResponse(BaseModel):
    id: str
    email: Optional[str] = None


class DocumentResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    storage_path: str
    page_count: Optional[int] = None
    status: str
    error: Optional[str] = None
    created_at: str


class DocumentDetailResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    page_count: Optional[int] = None
    status: str
    chunk_count: int = 0
    error: Optional[str] = None
    created_at: str


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]


class ChatRequest(BaseModel):
    document_id: str = Field(..., description="Target document UUID")
    question: str = Field(..., min_length=1, max_length=2000, description="User question about the document")


class Citation(BaseModel):
    ref: int = Field(..., description="Citation marker number matching [1], [2], etc.")
    chunk_id: str = Field(..., description="UUID of the chunk")
    page_start: int
    page_end: int
    snippet: str = Field(..., description="Best supporting sentences from the chunk")
    full_text: Optional[str] = Field(None, description="Complete text of the chunk")
    similarity: float = Field(..., description="Cosine similarity score")
    char_start: Optional[int] = Field(None, description="Start offset of snippet in full_text")
    char_end: Optional[int] = Field(None, description="End offset of snippet in full_text")
    context_before: Optional[str] = Field(None, description="Surrounding sentence before the snippet")
    context_after: Optional[str] = Field(None, description="Surrounding sentence after the snippet")


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
    found: bool = True

