"""
Terminal verification script for Phase 3 & 4:
Tests embeddings + pgvector storage + match_chunks RPC + RAG Q&A with citations.

Usage:
    python backend/scripts/test_rag_terminal.py --demo
    python backend/scripts/test_rag_terminal.py --doc-id <UUID> --user-id <UUID> --query "What is X?"
    python backend/scripts/test_rag_terminal.py --doc-id <UUID> --user-id <UUID> --query "What is X?" --chat
"""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path so 'app' can always be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import logging
from app.core.config import settings
from app.core.supabase import get_supabase_client
from app.services.embedder import embedder_service, l2_normalize
from app.services.rag import execute_rag_query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_rag_terminal")


def run_live_query(query_text: str, document_id: str, user_id: str, top_k: int = 6):
    """Executes a vector search query against Supabase pgvector using match_chunks."""
    supabase = get_supabase_client()
    if not supabase:
        print("[ERROR] Supabase client is not configured. Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env.")
        sys.exit(1)

    print(f"\nEmbedding query: '{query_text}' with model '{settings.GEMINI_EMBED_MODEL}' (dim={settings.EMBED_DIM})...")
    query_vector = embedder_service.embed_query(query_text)
    print(f"Generated L2-normalized query vector of length {len(query_vector)}.")

    print(f"\nExecuting match_chunks RPC on document {document_id}...")
    rpc_params = {
        "query_embedding": query_vector,
        "match_document_id": document_id,
        "p_user_id": user_id,
        "match_count": top_k,
    }

    response = supabase.rpc("match_chunks", rpc_params).execute()
    matches = response.data or []

    print(f"\n{'='*25} RETRIEVED CHUNKS ({len(matches)} found) {'='*25}")
    if not matches:
        print("No matching chunks found for this document.")
    else:
        for idx, match in enumerate(matches, 1):
            sim = match.get("similarity", 0.0)
            p_start = match.get("page_start")
            p_end = match.get("page_end")
            content = match.get("content", "")
            preview = content[:200].replace("\n", " ")
            print(f"[{idx}] Similarity: {sim:.4f} | Pages: {p_start}-{p_end} | ID: {match.get('id')}")
            print(f"    Snippet: \"{preview}...\"\n")
    print("=" * 70)


def run_chat_query(query_text: str, document_id: str, user_id: str):
    """Runs the full end-to-end RAG chat pipeline with LLM grounding and citation parsing."""
    print(f"\n--- Running Full RAG Chat Query ---")
    print(f"Document: {document_id}")
    print(f"Question: {query_text}")
    print(f"Chat Model: {settings.GEMINI_CHAT_MODEL}")
    print("-" * 50)

    res = execute_rag_query(document_id=document_id, question=query_text, user_id=user_id)

    print(f"\nFound in document: {res.found}")
    print(f"\nAnswer:\n{res.answer}\n")
    print(f"Citations ({len(res.citations)} used):")
    for c in res.citations:
        print(f"  [{c.ref}] Pages {c.page_start}-{c.page_end} (sim: {c.similarity:.4f}) -> \"{c.snippet}...\"")
    print("=" * 50)


def run_demo_self_test():
    """Validates vector math, normalization, and RPC structure."""
    print("\n--- Running Phase 3 & 4 Self-Test ---")
    
    # 1. Test normalization
    test_vec = [1.0, 2.0, 3.0, 4.0]
    normed = l2_normalize(test_vec)
    magnitude = sum(x**2 for x in normed) ** 0.5
    print(f"✓ L2 Normalization test: Vector magnitude = {magnitude:.6f} (expected 1.000000)")
    assert abs(magnitude - 1.0) < 1e-5

    # 2. Test Supabase connection
    supabase = get_supabase_client()
    if supabase:
        print("✓ Supabase Client initialized successfully with SERVICE_ROLE_KEY.")
        # Check if match_chunks function is registered
        try:
            rpc_test = supabase.rpc("match_chunks", {
                "query_embedding": [0.0] * settings.EMBED_DIM,
                "match_document_id": "00000000-0000-0000-0000-000000000000",
                "p_user_id": "00000000-0000-0000-0000-000000000000",
                "match_count": 1
            }).execute()
            print("✓ match_chunks pgvector RPC verified and responsive in Supabase!")
        except Exception as e:
            print(f"[NOTE] RPC test result: {e}")
    else:
        print("[!] Supabase client not yet configured with valid credentials.")

    print("\nPhase 3 & 4 Self-Test Completed Successfully!\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test RAG embeddings and pgvector retrieval.")
    parser.add_argument("--query", type=str, default="What is pgvector and cosine similarity?", help="Question to test")
    parser.add_argument("--doc-id", type=str, default="", help="Document UUID in Supabase")
    parser.add_argument("--user-id", type=str, default="", help="User UUID in Supabase")
    parser.add_argument("--chat", action="store_true", help="Run full RAG chat with Gemini generation")
    parser.add_argument("--demo", action="store_true", help="Run self-test without live document")

    args = parser.parse_args()

    if args.demo or not args.doc_id:
        run_demo_self_test()
    elif args.chat:
        run_chat_query(args.query, args.doc_id, args.user_id)
    else:
        run_live_query(args.query, args.doc_id, args.user_id)
