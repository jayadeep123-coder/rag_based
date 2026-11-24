"""
Unit and integration tests for document validation, PyMuPDF extraction,
page-aware chunking, and scanned PDF detection.
"""

import io
import pymupdf as fitz
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.ingest import process_pdf_text_and_chunk
from app.dependencies.auth import get_current_user


def create_in_memory_pdf(pages_text: list[str]) -> bytes:
    """Helper to generate a multi-page PDF in memory using PyMuPDF."""
    doc = fitz.open()
    for text in pages_text:
        page = doc.new_page(width=595, height=842)  # A4 size
        page.insert_text((50, 72), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_pdf_extraction_and_chunking_verification():
    """
    Tests text extraction from a 3-page in-memory PDF and verifies
    page-aware chunks are produced properly.
    """
    page1 = (
        "Chapter 1: Introduction to Distributed Systems and Microservices.\n\n"
        "Distributed systems consist of autonomous computing nodes communicating over a network. "
        "Each service maintains its own isolated database to ensure loose coupling."
    )
    page2 = (
        "Chapter 2: Vector Databases and Semantic Retrieval.\n\n"
        "PostgreSQL with pgvector provides cosine similarity indexing for dense vector embeddings. "
        "HNSW indexing drastically accelerates nearest neighbor queries at scale."
    )
    page3 = (
        "Chapter 3: Hallucination Mitigation in Retrieval Augmented Generation.\n\n"
        "Grounding responses strictly within retrieved numbered passages eliminates fabricated facts. "
        "Citation markers allow readers to verify claims against original sources."
    )

    pdf_bytes = create_in_memory_pdf([page1, page2, page3])
    chunks, error, page_count = process_pdf_text_and_chunk(pdf_bytes, "sample-doc-123")

    assert error is None
    assert page_count == 3
    assert chunks is not None
    assert len(chunks) >= 1

    # Verify content across pages
    all_content = " ".join(c.content for c in chunks)
    assert "Distributed systems" in all_content
    assert "pgvector" in all_content
    assert "Hallucination Mitigation" in all_content


def test_scanned_pdf_detection():
    """
    Tests that a PDF with no selectable text triggers the scanned PDF error.
    """
    # Create empty PDF page with no text
    doc = fitz.open()
    doc.new_page(width=595, height=842)
    empty_pdf_bytes = doc.tobytes()
    doc.close()

    chunks, error, page_count = process_pdf_text_and_chunk(empty_pdf_bytes, "scanned-doc-456")
    assert chunks is None
    assert page_count == 1
    assert error == "No extractable text (scanned PDF). OCR is not supported yet."


@pytest.mark.asyncio
async def test_upload_non_pdf_rejected():
    """Validates that non-PDF files are rejected with 400 Bad Request."""
    # Override auth dependency to simulate authenticated user
    app.dependency_overrides[get_current_user] = lambda: {"id": "user-123", "email": "test@example.com"}

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            files = {"file": ("test.txt", b"Hello world text file", "text/plain")}
            response = await ac.post("/api/documents/upload", files=files)
            assert response.status_code == 400
            assert "Only PDF documents" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_upload_corrupted_pdf_rejected():
    """Validates that files without %PDF- magic bytes are rejected with 400."""
    app.dependency_overrides[get_current_user] = lambda: {"id": "user-123", "email": "test@example.com"}

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # File named .pdf but with garbage bytes
            files = {"file": ("corrupted.pdf", b"NOT A VALID PDF HEADER", "application/pdf")}
            response = await ac.post("/api/documents/upload", files=files)
            assert response.status_code == 400
            assert "%PDF-" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_upload_oversized_file_rejected():
    """Validates that files > MAX_PDF_SIZE_MB are rejected with 413 Payload Too Large."""
    app.dependency_overrides[get_current_user] = lambda: {"id": "user-123", "email": "test@example.com"}

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # 11 MB dummy payload starting with %PDF-
            oversized_content = b"%PDF-" + b"0" * (11 * 1024 * 1024)
            files = {"file": ("large.pdf", oversized_content, "application/pdf")}
            response = await ac.post("/api/documents/upload", files=files)
            assert response.status_code == 413
            assert "10 MB" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
