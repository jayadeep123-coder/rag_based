"""
Model verification script for AI Mentor.
Validates Gemini embedding and chat model availability, supported methods,
vector dimension, L2 normalization, and basic chat generation.

Usage:
    python backend/scripts/check_models.py
"""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path so 'app' can always be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from app.core.config import settings
from app.services.embedder import l2_normalize
from google import genai
from google.genai import types


def check_models():
    print("=" * 60)
    print("AI Mentor: Google Gemini Model Verification")
    print("=" * 60)

    # 1. Validate environment configuration
    api_key = settings.GEMINI_API_KEY
    if not api_key or api_key.startswith("PASTE_"):
        print("[ERROR] GEMINI_API_KEY is missing or unconfigured in backend/.env.")
        sys.exit(1)

    embed_model_name = settings.GEMINI_EMBED_MODEL.strip()
    chat_model_name = settings.GEMINI_CHAT_MODEL.strip()
    embed_dim = settings.EMBED_DIM

    if not embed_model_name:
        print("[ERROR] GEMINI_EMBED_MODEL environment variable is missing or empty.")
        sys.exit(1)

    if not chat_model_name:
        print("[ERROR] GEMINI_CHAT_MODEL environment variable is missing or empty.")
        sys.exit(1)

    print(f"[CONFIG] Configured Embedding Model: {embed_model_name}")
    print(f"[CONFIG] Configured Chat Model:      {chat_model_name}")
    print(f"[CONFIG] Target Embedding Dimension: {embed_dim}")
    print("-" * 60)

    client = genai.Client(api_key=api_key)

    # 2. List available models and check support
    print("[1/4] Querying available models from Gemini API...")
    try:
        available_models = list(client.models.list())
    except Exception as e:
        print(f"[ERROR] Failed to query Gemini models: {e}")
        sys.exit(1)

    model_map = {}
    embedding_alternatives = []
    flash_alternatives = []

    for m in available_models:
        clean_name = m.name.removeprefix("models/")
        actions = getattr(m, "supported_actions", []) or []
        model_map[clean_name] = actions

        if "embedding" in clean_name or "embedContent" in actions:
            embedding_alternatives.append(clean_name)
        if "flash" in clean_name or "generateContent" in actions:
            flash_alternatives.append(clean_name)

    # Verify Embedding Model
    clean_embed = embed_model_name.removeprefix("models/")
    if clean_embed not in model_map:
        print(f"\n[ERROR] Embedding model '{embed_model_name}' was NOT found.")
        print(f"Closest available models supporting embedding:")
        for alt in embedding_alternatives:
            print(f"  - {alt}")
        sys.exit(1)

    if "embedContent" not in model_map[clean_embed]:
        print(f"\n[ERROR] Model '{embed_model_name}' does not support 'embedContent'. Supported: {model_map[clean_embed]}")
        print(f"Available embedding models:")
        for alt in embedding_alternatives:
            print(f"  - {alt}")
        sys.exit(1)

    print(f"  ✓ Embedding model '{embed_model_name}' verified and supports 'embedContent'.")

    # Verify Chat Model
    clean_chat = chat_model_name.removeprefix("models/")
    if clean_chat not in model_map:
        print(f"\n[ERROR] Chat model '{chat_model_name}' was NOT found.")
        print(f"Closest available models containing 'flash':")
        for alt in flash_alternatives:
            print(f"  - {alt}")
        sys.exit(1)

    if "generateContent" not in model_map[clean_chat]:
        print(f"\n[ERROR] Model '{chat_model_name}' does not support 'generateContent'. Supported: {model_map[clean_chat]}")
        print(f"Available generative models:")
        for alt in flash_alternatives:
            print(f"  - {alt}")
        sys.exit(1)

    print(f"  ✓ Chat model '{chat_model_name}' verified and supports 'generateContent'.")

    # 3. Test Embedding Sentence and Vector Dimension
    print(f"\n[2/4] Generating test embedding with task_type=RETRIEVAL_DOCUMENT and output_dimensionality={embed_dim}...")
    test_sentence = "This is a test sentence to verify Gemini embeddings for the AI Mentor RAG pipeline."
    try:
        embed_response = client.models.embed_content(
            model=clean_embed,
            contents=test_sentence,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=embed_dim,
            )
        )

        if hasattr(embed_response, "embedding") and embed_response.embedding:
            raw_vector = embed_response.embedding.values
        elif hasattr(embed_response, "embeddings") and embed_response.embeddings:
            raw_vector = embed_response.embeddings[0].values
        else:
            raise RuntimeError(f"Unexpected embed response structure: {embed_response}")

        vector_len = len(raw_vector)
        print(f"  ✓ Received embedding vector length: {vector_len}")

        if vector_len != embed_dim:
            print(f"[ERROR] Embedding length ({vector_len}) does not match target EMBED_DIM ({embed_dim})!")
            sys.exit(1)
        print(f"  ✓ Embedding vector dimension correctly matches EMBED_DIM ({embed_dim}).")

    except Exception as e:
        print(f"[ERROR] Failed to generate test embedding: {e}")
        sys.exit(1)

    # 4. Test L2-normalization
    print("\n[3/4] Performing L2 vector normalization...")
    normalized_vec = l2_normalize(raw_vector)
    norm_val = float(np.linalg.norm(np.array(normalized_vec, dtype=np.float32)))
    print(f"  ✓ Normalized vector Euclidean norm: {norm_val:.6f} (expected: ~1.000000)")
    if abs(norm_val - 1.0) > 1e-4:
        print(f"[ERROR] L2 normalized vector magnitude ({norm_val}) is not 1.0!")
        sys.exit(1)

    # 5. Test Chat Model
    print(f"\n[4/4] Sending short test prompt to chat model '{chat_model_name}'...")
    try:
        chat_prompt = "Reply with exactly three words confirming you are ready to mentor."
        chat_response = client.models.generate_content(
            model=clean_chat,
            contents=chat_prompt
        )
        reply = chat_response.text.strip() if chat_response and chat_response.text else "(No reply)"
        print(f"  ✓ Chat model response: \"{reply}\"")
    except Exception as e:
        print(f"[ERROR] Failed to get response from chat model '{chat_model_name}': {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("SUCCESS: All models verified and operational for AI Mentor!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    check_models()

