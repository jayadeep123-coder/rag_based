"""
Unit and integration tests for RAG query flow, citation parsing,
not-found fallback behavior, and /api/chat endpoint.
"""

import pytest
from unittest.mock import MagicMock, patch
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.rag import (
    extract_citation_refs,
    build_context_prompt,
    execute_rag_query,
    select_best_supporting_sentences,
    NOT_FOUND_RESPONSE,
)
from app.dependencies.auth import get_current_user


def test_citation_ref_parsing():
    text = "Machine learning models rely on statistical representations [1]. Deep networks scale this further [2][3]."
    refs = extract_citation_refs(text)
    assert refs == [1, 2, 3]


def test_citation_ref_parsing_duplicates():
    text = "First claim [1]. Second claim repeated [1] and another [2]."
    refs = extract_citation_refs(text)
    assert refs == [1, 2]


def test_citation_ref_parsing_none():
    text = "No citations here."
    refs = extract_citation_refs(text)
    assert refs == []


def test_build_context_prompt():
    chunks = [
        {"page_start": 1, "page_end": 1, "content": "Text of chunk one."},
        {"page_start": 2, "page_end": 3, "content": "Text of chunk two."},
    ]
    prompt = build_context_prompt(chunks)
    assert "Passage [1] (Pages 1-1):" in prompt
    assert "Text of chunk one." in prompt
    assert "Passage [2] (Pages 2-3):" in prompt
    assert "Text of chunk two." in prompt


def test_rag_fallback_below_similarity_threshold():
    """
    Verifies that when top retrieved chunks are below SIMILARITY_THRESHOLD (e.g. 0.45),
    execute_rag_query immediately returns found=False without hallucinating or calling the chat LLM.
    """
    low_sim_chunks = [
        {"id": "c1", "similarity": 0.25, "page_start": 1, "page_end": 1, "content": "Unrelated passage."},
        {"id": "c2", "similarity": 0.31, "page_start": 2, "page_end": 2, "content": "Another irrelevant piece."}
    ]

    mock_supabase = MagicMock()
    # Mock match_chunks RPC call returning low-similarity chunks
    mock_supabase.rpc.return_value.execute.return_value.data = low_sim_chunks
    # Mock query_logs insert
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()

    with patch("app.services.rag.get_supabase_client", return_value=mock_supabase), \
         patch("app.services.rag.embedder_service.embed_query", return_value=[0.1] * 768), \
         patch("app.services.rag.genai.Client") as mock_genai:

        response = execute_rag_query(
            document_id="doc-123",
            question="What is quantum gravity?",
            user_id="user-123",
            similarity_threshold=0.45
        )

        assert response.found is False
        assert response.answer == NOT_FOUND_RESPONSE
        assert response.citations == []
        # Ensure LLM was NEVER called
        mock_genai.assert_not_called()


@pytest.mark.asyncio
async def test_api_chat_unauthorized():
    """Calling POST /api/chat without authentication returns 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/chat", json={"document_id": "doc-1", "question": "What is AI?"})
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_api_chat_validation_error():
    """Empty question or missing document_id returns 422 Unprocessable Entity."""
    app.dependency_overrides[get_current_user] = lambda: {"id": "user-123", "email": "test@example.com"}
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.post("/api/chat", json={"document_id": "doc-1", "question": ""})
            assert res.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_select_best_supporting_sentences():
    chunk_text = (
        "Infrastructure costs represent a significant portion of datacenter expenditure. "
        "Hypervisors allow multiple virtual machines to share underlying hardware resources. "
        "Type-1 hypervisors run directly on bare metal without a host operating system. "
        "Energy efficiency remains a major challenge in modern cloud facilities."
    )
    question = "What is a hypervisor and how does it work?"
    answer = "Hypervisors enable multiple VMs to run on shared hardware [1]."

    snippet, full_text, ctx_before, ctx_after, start, end = select_best_supporting_sentences(
        chunk_text, question, answer, ref=1
    )
    # The snippet should prioritize the sentences mentioning hypervisors, not infrastructure costs or energy
    assert "Hypervisors allow multiple virtual machines" in snippet
    assert "Type-1 hypervisors" in snippet
    assert "Infrastructure costs" not in snippet
    assert "Energy efficiency" not in snippet
    assert ctx_before is not None
    assert "Infrastructure costs" in ctx_before
    assert ctx_after is not None
    assert "Energy efficiency" in ctx_after
    assert start is not None and end is not None
    assert start > 0
    assert full_text == chunk_text.strip()


def test_clean_passage_and_slide_splitting():
    from app.services.rag import clean_passage_text, extract_candidate_sentences

    # Test table-like short lines collapsed into single line with pipes
    table_raw = (
        "Summary Header:\n"
        "Docker\n"
        "Run\n"
        "(launch)\n"
        "Docker\n"
        "ps\n"
        "Docker\n"
        "Stop\n"
        "Next normal sentence in the passage."
    )
    cleaned = clean_passage_text(table_raw)
    assert "Docker | Run | (launch) | Docker | ps | Docker | Stop" in cleaned

    # Test slide-style bullet points without terminal periods
    slide_raw = (
        "• Common Docker Commands: Docker Run to launch containers and Docker Pull to fetch images.\n"
        "- Scalability: Offers horizontal pod scaling based on incoming dynamic traffic.\n"
        "* Use Cases: Applied in microservices and cloud-native systems."
    )
    candidates = extract_candidate_sentences(slide_raw)
    assert len(candidates) == 3
    # Verify bullets are stripped from candidates
    for cand in candidates:
        assert not cand.startswith("•")
        assert not cand.startswith("-")
        assert not cand.startswith("*")
        assert len(cand) >= 25

