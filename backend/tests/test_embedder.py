"""
Unit tests for the Gemini embedder service (backend/app/services/embedder.py).
Tests L2 normalization, batch chunking, and vector dimensional constraints.
"""

import math
import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from app.services.embedder import l2_normalize, GeminiEmbedder


def test_l2_normalization_math():
    # 3-4-5 right triangle: norm of [3.0, 4.0] is 5.0
    vec = [3.0, 4.0]
    normed = l2_normalize(vec)
    assert pytest.approx(normed[0], 0.001) == 0.6
    assert pytest.approx(normed[1], 0.001) == 0.8

    # Check norm is 1.0
    norm_val = np.linalg.norm(np.array(normed))
    assert pytest.approx(norm_val, 0.001) == 1.0


def test_l2_normalize_zero_vector():
    zero_vec = [0.0, 0.0, 0.0]
    normed = l2_normalize(zero_vec)
    assert normed == [0.0, 0.0, 0.0]


def test_embedder_batching():
    """Verifies that large lists of chunks are properly partitioned into batches."""
    embedder = GeminiEmbedder(api_key="mock-key", model="test-embedding-model", dim=768)

    # Mock _embed_batch_with_retry to avoid calling live API
    sample_emb = [0.1] * 768

    def mock_embed_batch(texts, task_type):
        assert task_type == "RETRIEVAL_DOCUMENT"
        assert len(texts) <= 50  # Must adhere to EMBEDDING_BATCH_SIZE
        return [sample_emb for _ in texts]

    with patch.object(embedder, "_embed_batch_with_retry", side_effect=mock_embed_batch):
        # 125 documents should produce 3 batches (50, 50, 25)
        dummy_docs = [f"Text chunk {i}" for i in range(125)]
        embeddings = embedder.embed_documents(dummy_docs)

        assert len(embeddings) == 125
        assert len(embeddings[0]) == 768


def test_embed_query_empty_error():
    embedder = GeminiEmbedder(api_key="mock-key")
    with pytest.raises(ValueError, match="cannot be empty"):
        embedder.embed_query("   ")

