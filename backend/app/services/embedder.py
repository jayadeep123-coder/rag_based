"""
Google Gemini Embedding Service via the official google-genai SDK.
Handles:
1. Document chunk embedding (task_type=RETRIEVAL_DOCUMENT)
2. Query embedding (task_type=RETRIEVAL_QUERY)
3. Output dimensionality reduction and L2 normalization
4. Batching and exponential backoff retry for rate limits
"""

import time
import math
import logging
from typing import List, Optional
import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google import genai
from google.genai import types
from app.core.config import settings

logger = logging.getLogger("embedder")

# Max texts allowed per Gemini embed_content request
EMBEDDING_BATCH_SIZE = 50


def l2_normalize(vector: List[float]) -> List[float]:
    """
    Applies L2 normalization to a vector: v / ||v||_2.
    Ensures cosine similarity is mathematically valid when dimensionality is reduced.
    """
    arr = np.array(vector, dtype=np.float32)
    norm = np.linalg.norm(arr)
    if norm == 0 or math.isnan(norm):
        return vector
    normalized = arr / norm
    return normalized.tolist()


class GeminiEmbedder:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, dim: Optional[int] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_EMBED_MODEL
        self.dim = dim or settings.EMBED_DIM
        self._client: Optional[genai.Client] = None

    @property
    def client(self) -> genai.Client:
        if not self._client:
            if not self.api_key or self.api_key.startswith("PASTE_"):
                raise ValueError("GEMINI_API_KEY is not configured in backend/.env")
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True
    )
    def _embed_batch_with_retry(
        self,
        texts: List[str],
        task_type: str
    ) -> List[List[float]]:
        """Calls Gemini embed_content API with retry and exponential backoff for rate limits."""
        config = types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=self.dim,
        )

        response = self.client.models.embed_content(
            model=self.model,
            contents=texts,
            config=config
        )

        embeddings: List[List[float]] = []
        if hasattr(response, "embeddings") and response.embeddings:
            for emb in response.embeddings:
                values = emb.values
                # Apply L2 normalization
                embeddings.append(l2_normalize(values))
        elif hasattr(response, "embedding") and response.embedding:
            # Single item response
            embeddings.append(l2_normalize(response.embedding.values))
        else:
            raise RuntimeError(f"Unexpected response format from Gemini embed_content: {response}")

        return embeddings

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of document chunk texts using RETRIEVAL_DOCUMENT.
        Splits into batches to stay within API limits.
        """
        if not texts:
            return []

        all_embeddings: List[List[float]] = []
        total_batches = math.ceil(len(texts) / EMBEDDING_BATCH_SIZE)

        for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch = texts[i:i + EMBEDDING_BATCH_SIZE]
            batch_num = (i // EMBEDDING_BATCH_SIZE) + 1
            logger.info(f"Embedding batch {batch_num}/{total_batches} ({len(batch)} chunks)...")

            batch_embeddings = self._embed_batch_with_retry(
                texts=batch,
                task_type="RETRIEVAL_DOCUMENT"
            )
            all_embeddings.extend(batch_embeddings)

            # Modest delay between batches to respect rate limits
            if i + EMBEDDING_BATCH_SIZE < len(texts):
                time.sleep(0.2)

        return all_embeddings

    def embed_query(self, query: str) -> List[float]:
        """
        Embeds a single search question using RETRIEVAL_QUERY.
        Returns the L2-normalized embedding vector.
        """
        if not query.strip():
            raise ValueError("Query string cannot be empty.")

        embeddings = self._embed_batch_with_retry(
            texts=[query.strip()],
            task_type="RETRIEVAL_QUERY"
        )
        return embeddings[0]


embedder_service = GeminiEmbedder()

