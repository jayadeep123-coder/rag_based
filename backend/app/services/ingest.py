"""
PDF ingestion pipeline service.
Handles:
1. Downloading PDF from Supabase Storage.
2. Per-page text extraction with PyMuPDF.
3. Text cleaning and scanned PDF detection.
4. Calling the page-aware chunker.
5. Generating Gemini vector embeddings via embedder_service.
6. Bulk inserting chunks into Supabase pgvector and setting status to 'ready'.
"""

import os
import tempfile
import logging
from typing import List, Tuple, Optional
import pymupdf as fitz
from app.core.supabase import get_supabase_client
from app.services.chunker import PageText, TextChunk, clean_text, chunk_pages
from app.services.embedder import embedder_service

logger = logging.getLogger("ingestion")
logging.basicConfig(level=logging.INFO)

SCANNED_PDF_MIN_CHARS = 50
CHUNK_INSERT_BATCH_SIZE = 50


def extract_pages_from_pdf(pdf_bytes: bytes) -> List[PageText]:
    """
    Extracts text per page using PyMuPDF from an ephemeral temporary file.
    Cleans up temp file in finally block to ensure memory and ephemeral disk are safely released.
    """
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(pdf_bytes)
            tmp.flush()

        doc = fitz.open(tmp_path)
        pages: List[PageText] = []

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_num = page_idx + 1
            raw_text = page.get_text("text")
            cleaned = clean_text(raw_text)
            pages.append(PageText(page_number=page_num, text=cleaned))
            page = None

        doc.close()
        return pages
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def process_pdf_text_and_chunk(
    pdf_bytes: bytes,
    document_id: str,
) -> Tuple[Optional[List[TextChunk]], Optional[str], int]:
    """
    Parses PDF bytes, validates selectable text, and generates chunks.
    
    Returns:
        (chunks, error_message, page_count)
        If scanned PDF or no text, returns (None, error_message, page_count).
    """
    try:
        pages = extract_pages_from_pdf(pdf_bytes)
        page_count = len(pages)
        
        # Check total extracted characters across all pages
        total_chars = sum(len(p.text) for p in pages)
        logger.info(f"Document {document_id}: Extracted {page_count} pages with {total_chars} total characters.")

        if total_chars < SCANNED_PDF_MIN_CHARS:
            error_msg = "No extractable text (scanned PDF). OCR is not supported yet."
            logger.warning(f"Document {document_id} failed: {error_msg}")
            return None, error_msg, page_count

        # Chunk pages using page-aware chunker
        chunks = chunk_pages(pages)
        logger.info(f"Document {document_id}: Successfully created {len(chunks)} chunks across {page_count} pages.")
        return chunks, None, page_count

    except Exception as e:
        error_msg = f"Failed to parse PDF: {str(e)}"
        logger.error(f"Document {document_id} exception: {error_msg}")
        return None, error_msg, 0


async def process_pdf_ingestion(
    document_id: str,
    user_id: str,
    storage_path: str,
) -> None:
    """
    FastAPI BackgroundTask worker for document ingestion:
    1. Downloads PDF from Supabase Storage.
    2. Extracts text and chunks pages.
    3. Generates Gemini vector embeddings.
    4. Inserts chunks in batches into Supabase pgvector chunks table.
    5. Updates database status to 'ready' (or 'failed' on error).
    """
    supabase = get_supabase_client()
    if not supabase:
        logger.error("Supabase client not initialized during background ingestion.")
        return

    try:
        # 1. Download PDF from Supabase Storage 'pdfs' bucket
        logger.info(f"Downloading {storage_path} from Supabase Storage...")
        file_bytes = supabase.storage.from_("pdfs").download(storage_path)

        # 2. Extract and chunk
        chunks, error, page_count = process_pdf_text_and_chunk(file_bytes, document_id)

        if error:
            # Mark document as failed with clear error
            supabase.table("documents").update({
                "status": "failed",
                "error": error,
                "page_count": page_count,
            }).eq("id", document_id).execute()
            return

        if not chunks:
            supabase.table("documents").update({
                "status": "failed",
                "error": "No chunks generated from document.",
                "page_count": page_count,
            }).eq("id", document_id).execute()
            return

        # 3. Generate Gemini vector embeddings (RETRIEVAL_DOCUMENT)
        logger.info(f"Document {document_id}: Generating embeddings for {len(chunks)} chunks...")
        chunk_texts = [c.content for c in chunks]
        embeddings = embedder_service.embed_documents(chunk_texts)

        if len(embeddings) != len(chunks):
            raise RuntimeError(f"Embedding count mismatch: expected {len(chunks)}, got {len(embeddings)}")

        # 4. Prepare chunk records for bulk insertion
        chunk_records = []
        for chunk, emb in zip(chunks, embeddings):
            chunk_records.append({
                "document_id": document_id,
                "user_id": user_id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "token_estimate": chunk.token_estimate,
                "embedding": emb,
            })

        # Insert chunks in batches
        logger.info(f"Document {document_id}: Inserting {len(chunk_records)} chunks into Supabase...")
        for i in range(0, len(chunk_records), CHUNK_INSERT_BATCH_SIZE):
            batch = chunk_records[i:i + CHUNK_INSERT_BATCH_SIZE]
            insert_res = supabase.table("chunks").insert(batch).execute()
            if not insert_res.data:
                logger.warning(f"Batch insert from {i} returned no data.")

        # 5. Update document status to ready
        supabase.table("documents").update({
            "status": "ready",
            "page_count": page_count,
            "error": None,
        }).eq("id", document_id).execute()

        logger.info(f"Document {document_id} ingestion complete! Status marked as READY.")

    except Exception as e:
        logger.exception(f"Unhandled error ingesting document {document_id}: {str(e)}")
        if supabase:
            supabase.table("documents").update({
                "status": "failed",
                "error": f"Internal ingestion error: {str(e)}",
            }).eq("id", document_id).execute()
