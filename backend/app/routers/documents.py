"""
FastAPI router for document management:
- Upload PDF with 20MB validation & magic byte verification
- List user documents
- Get document details & chunk count
- Delete document and storage file
"""

import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from app.dependencies.auth import get_current_user
from app.core.config import settings
from app.core.supabase import get_supabase_client
from app.models.schemas import DocumentResponse, DocumentListResponse, DocumentDetailResponse
from app.services.ingest import process_pdf_ingestion

router = APIRouter(prefix="/api/documents", tags=["Documents"])

PDF_MAGIC_BYTES = b"%PDF-"


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Uploads a PDF file with configurable size limit (default 10 MB)
    and user document quota limit (default 5 documents).
    Validates magic bytes, stores in Supabase Storage under {user_id}/{document_id}.pdf,
    records document with status 'processing', and launches background ingestion.
    """
    user_id = current_user["id"]
    filename = file.filename or "document.pdf"

    # 1. Validate file extension
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF documents (.pdf) are accepted."
        )

    # 2. Read contents and validate file size & magic bytes
    max_file_size_bytes = settings.MAX_PDF_SIZE_MB * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_PDF_SIZE_MB} MB (got {len(contents) / (1024*1024):.2f} MB)."
        )

    if not contents.startswith(PDF_MAGIC_BYTES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corrupted or invalid PDF header. Expected '%PDF-' magic bytes."
        )

    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Storage service not configured."
        )

    # 3. Enforce user document quota limit
    doc_count_res = supabase.table("documents").select("id", count="exact").eq("user_id", user_id).execute()
    existing_count = doc_count_res.count if doc_count_res.count is not None else 0
    if existing_count >= settings.MAX_DOCS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document limit reached ({settings.MAX_DOCS_PER_USER} documents maximum per user). Please delete an existing document before uploading a new one."
        )

    # 3. Create document record and storage path
    document_id = str(uuid.uuid4())
    storage_path = f"{user_id}/{document_id}.pdf"

    try:
        # Upload binary stream to Supabase Storage
        supabase.storage.from_("pdfs").upload(
            path=storage_path,
            file=contents,
            file_options={"content-type": "application/pdf"}
        )

        # Insert record in public.documents table
        insert_res = supabase.table("documents").insert({
            "id": document_id,
            "user_id": user_id,
            "filename": filename,
            "storage_path": storage_path,
            "status": "processing",
        }).execute()

        if not insert_res.data:
            raise RuntimeError("Database did not return inserted document row.")

        created_doc = insert_res.data[0]

        # 4. Enqueue background ingestion pipeline
        background_tasks.add_task(
            process_pdf_ingestion,
            document_id=document_id,
            user_id=user_id,
            storage_path=storage_path
        )

        return DocumentResponse(
            id=created_doc["id"],
            user_id=created_doc["user_id"],
            filename=created_doc["filename"],
            storage_path=created_doc["storage_path"],
            page_count=created_doc.get("page_count"),
            status=created_doc["status"],
            error=created_doc.get("error"),
            created_at=str(created_doc["created_at"])
        )

    except Exception as e:
        # Cleanup storage file if record insertion failed
        try:
            supabase.storage.from_("pdfs").remove([storage_path])
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process and store PDF: {str(e)}"
        )


@router.get("", response_model=DocumentListResponse)
async def list_documents(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Lists all documents belonging to the authenticated user."""
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database client not configured.")

    res = supabase.table("documents") \
        .select("*") \
        .eq("user_id", current_user["id"]) \
        .order("created_at", desc=True) \
        .execute()

    docs = [
        DocumentResponse(
            id=d["id"],
            user_id=d["user_id"],
            filename=d["filename"],
            storage_path=d["storage_path"],
            page_count=d.get("page_count"),
            status=d["status"],
            error=d.get("error"),
            created_at=str(d["created_at"])
        )
        for d in (res.data or [])
    ]
    return DocumentListResponse(documents=docs)


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Retrieves document status, page count, and total chunk count."""
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database client not configured.")

    doc_res = supabase.table("documents") \
        .select("*") \
        .eq("id", document_id) \
        .eq("user_id", current_user["id"]) \
        .execute()

    if not doc_res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    doc = doc_res.data[0]

    # Count associated chunks
    chunk_res = supabase.table("chunks") \
        .select("id", count="exact") \
        .eq("document_id", document_id) \
        .execute()

    chunk_count = chunk_res.count if chunk_res.count is not None else 0

    return DocumentDetailResponse(
        id=doc["id"],
        user_id=doc["user_id"],
        filename=doc["filename"],
        page_count=doc.get("page_count"),
        status=doc["status"],
        chunk_count=chunk_count,
        error=doc.get("error"),
        created_at=str(doc["created_at"])
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Deletes a document row, all cascading chunks, and the file in Supabase Storage."""
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database client not configured.")

    # 1. Fetch document to verify ownership and find storage path
    doc_res = supabase.table("documents") \
        .select("storage_path") \
        .eq("id", document_id) \
        .eq("user_id", current_user["id"]) \
        .execute()

    if not doc_res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    storage_path = doc_res.data[0].get("storage_path")

    # 2. Delete storage file
    if storage_path:
        try:
            supabase.storage.from_("pdfs").remove([storage_path])
        except Exception:
            pass

    # 3. Delete document row from Postgres (chunks are deleted via CASCADE)
    supabase.table("documents") \
        .delete() \
        .eq("id", document_id) \
        .eq("user_id", current_user["id"]) \
        .execute()

    return {"success": True}


@router.post("/{document_id}/retry", response_model=DocumentResponse)
async def retry_document_ingestion(
    document_id: str,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retries ingestion for an interrupted or failed document.
    Deletes partial chunks, resets status to 'processing', and re-launches the ingestion pipeline.
    """
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database client not configured.")

    doc_res = (
        supabase.table("documents")
        .select("*")
        .eq("id", document_id)
        .eq("user_id", current_user["id"])
        .execute()
    )

    if not doc_res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    doc = doc_res.data[0]
    storage_path = doc.get("storage_path")

    if not storage_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Storage file path missing for this document. Please re-upload the document."
        )

    # 1. Delete any leftover partial chunks
    supabase.table("chunks").delete().eq("document_id", document_id).execute()

    # 2. Reset document status to processing
    supabase.table("documents").update({
        "status": "processing",
        "error": None
    }).eq("id", document_id).execute()

    # 3. Enqueue background ingestion worker
    background_tasks.add_task(
        process_pdf_ingestion,
        document_id=document_id,
        user_id=current_user["id"],
        storage_path=storage_path
    )

    return DocumentResponse(
        id=doc["id"],
        user_id=doc["user_id"],
        filename=doc["filename"],
        storage_path=storage_path,
        page_count=doc.get("page_count"),
        status="processing",
        error=None,
        created_at=str(doc["created_at"])
    )
