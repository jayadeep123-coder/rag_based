"""
RAG query and citation resolution service.
Executes vector retrieval, similarity threshold filtering, Gemini LLM prompting,
citation marker extraction, and telemetry query logging.
"""

import re
import time
import logging
from typing import List, Dict, Any, Tuple, Optional
from fastapi import HTTPException, status
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings
from app.core.supabase import get_supabase_client
from app.services.embedder import embedder_service
from app.models.schemas import ChatResponse, Citation
from google import genai
from google.genai import types

logger = logging.getLogger("rag")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def call_gemini_generate_with_retry(client: genai.Client, model: str, contents: str, config: types.GenerateContentConfig):
    """Executes Gemini generation with exponential backoff retry for transient network and 5xx errors."""
    return client.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )

SYSTEM_PROMPT = (
    "You are a study mentor. Answer the question using ONLY the numbered context passages provided. "
    "After each claim, cite the passage number like [1] or [2][3]. "
    "If the context does not contain the answer, say you could not find it in the document. "
    "Do not use outside knowledge. Keep answers clear and well structured; "
    "use short examples only if they appear in the context. "
    "Use standard Markdown: '-' for bullets, indent nested bullets by two spaces, and do not use '*' for bullets."
)

NOT_FOUND_RESPONSE = "I couldn't find this in the uploaded document."

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does",
    "doesn't", "doing", "don't", "down", "during", "each", "few", "for", "from", "further", "had",
    "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll",
    "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me",
    "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only",
    "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's",
    "the", "their", "theirs", "them", "themselves", "then", "there", "there's", "these", "they", "they'd",
    "they'll", "they're", "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's",
    "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with",
    "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself",
}


def extract_keywords(text: str) -> set:
    """Extracts non-stopword alphanumeric keywords of length >= 3 in lower case."""
    words = re.findall(r'[a-zA-Z0-9_\-]+', text.lower())
    return {w for w in words if len(w) >= 3 and w not in STOPWORDS}


STRIP_PUNCT_CHARS = ' \t\r\n"\'“”‘’`«»•·▪-*–—\u2022\u00b7\u25aa\u25ab\u25cf\u2023\u25e6\u2043\u2219:;.,'


def strip_bullets_and_quotes(text: str) -> str:
    """Removes stray leading/trailing quote marks, bullet characters, colons, and whitespace."""
    return text.strip(STRIP_PUNCT_CHARS).strip()


def clean_passage_text(text: str) -> str:
    """
    Cleans passage text:
    1. Detects table/column-like blocks (many short lines <= 15 chars), joins them with ' | ',
       and caps that portion at ~200 characters to eliminate one-word-per-line cascades.
    2. Collapses single newlines within a paragraph into spaces.
    3. Collapses runs of whitespace into a single space.
    4. Preserves paragraph breaks (double newlines).
    """
    if not text:
        return ""

    raw_lines = text.splitlines()
    cleaned_lines = []
    short_line_buf: List[str] = []

    def flush_table_buffer(buf: List[str]) -> str:
        if not buf:
            return ""
        short_count = sum(1 for line in buf if len(line.strip()) <= 15)
        # If there are >= 3 lines and >= 50% are short (<= 15 chars)
        if len(buf) >= 3 and (short_count / len(buf)) >= 0.5:
            joined = " | ".join(line.strip() for line in buf if line.strip())
            if len(joined) > 200:
                joined = joined[:197] + "..."
            return joined
        return "\n".join(buf)

    for line in raw_lines:
        stripped = line.strip()
        if stripped and len(stripped) <= 15:
            short_line_buf.append(stripped)
        else:
            if short_line_buf:
                flushed = flush_table_buffer(short_line_buf)
                if flushed:
                    cleaned_lines.append(flushed)
                short_line_buf = []
            if stripped:
                cleaned_lines.append(stripped)
            else:
                cleaned_lines.append("")

    if short_line_buf:
        flushed = flush_table_buffer(short_line_buf)
        if flushed:
            cleaned_lines.append(flushed)

    combined_text = "\n".join(cleaned_lines)

    # Split by multiple newlines (paragraphs)
    paragraphs = re.split(r'\n{2,}', combined_text)
    cleaned_paragraphs = []
    for p in paragraphs:
        # Collapse single newlines inside a paragraph into a single space
        p_collapsed = re.sub(r'(?<!\n)\n(?!\n)', ' ', p)
        # Collapse multiple whitespace characters into single space
        p_clean = re.sub(r'[ \t]+', ' ', p_collapsed).strip()
        if p_clean:
            cleaned_paragraphs.append(p_clean)

    return "\n\n".join(cleaned_paragraphs)


def split_long_candidate(cand: str, max_len: int = 300, target_wrap: int = 250) -> List[str]:
    """
    If a candidate is longer than ~300 characters, splits it at commas/semicolons
    or hard-wraps near a word boundary around 250 characters.
    """
    if len(cand) <= max_len:
        return [cand]

    sub_candidates: List[str] = []
    remaining = cand
    while len(remaining) > max_len:
        cut_idx = -1
        # Try finding semicolon or comma between index 150 and target_wrap + 30
        for sep in ['; ', ', ']:
            idx = remaining.rfind(sep, 150, target_wrap + 30)
            if idx != -1:
                cut_idx = idx + len(sep)
                break
        if cut_idx == -1:
            # Try finding whitespace near word boundary around target_wrap
            idx = remaining.rfind(' ', 150, target_wrap + 30)
            if idx != -1:
                cut_idx = idx + 1
            else:
                cut_idx = target_wrap

        piece = remaining[:cut_idx].strip()
        if piece:
            sub_candidates.append(piece)
        remaining = remaining[cut_idx:].strip()

    if remaining:
        sub_candidates.append(remaining)

    return sub_candidates


def extract_candidate_sentences(text: str) -> List[str]:
    """
    Extracts candidate sentences for slide-style PDFs and document passages:
    - Splits on sentence-ending punctuation (. , ? , ! followed by space/newline), newlines,
      and bullet characters (•, ·, ▪, -, *, etc.).
    - Trims whitespace and drops fragments shorter than ~25 characters.
    - If a candidate is longer than ~300 characters, splits it at commas/semicolons or word boundary.
    - Strips stray leading/trailing quotes and bullets.
    """
    cleaned = clean_passage_text(text)

    # Split pattern: sentence boundaries, newlines, or bullets
    split_pattern = r'(?:[.!?]+(?:\s+|\n+)|[\r\n]+|[•·▪\u2022\u00b7\u25aa\u25ab\u25cf\u2023\u25e6\u2043\u2219]|(?<=\s)[-*](?=\s)|^(?:[-*])\s+)'
    raw_segments = re.split(split_pattern, cleaned)

    candidates: List[str] = []
    for seg in raw_segments:
        cand = strip_bullets_and_quotes(seg)
        if len(cand) < 25:
            continue
        if len(cand) > 300:
            for sub in split_long_candidate(cand):
                sub_clean = strip_bullets_and_quotes(sub)
                if len(sub_clean) >= 25:
                    candidates.append(sub_clean)
        else:
            candidates.append(cand)

    if not candidates and cleaned.strip():
        fallback = strip_bullets_and_quotes(cleaned)
        if fallback:
            candidates.append(fallback[:300])

    return candidates


def select_best_supporting_sentences(
    chunk_text: str,
    question: str,
    answer: str,
    ref: int,
    max_sentences: int = 3,
) -> Tuple[str, str, Optional[str], Optional[str], Optional[int], Optional[int]]:
    """
    Extracts top 1-3 supporting candidate sentences from chunk_text for [ref].
    Scores candidates against question AND answer text (keyword overlap with stopwords removed).
    Returns (snippet, full_cleaned_text, context_before, context_after, char_start, char_end).
    """
    cleaned_full_text = clean_passage_text(chunk_text)
    if not cleaned_full_text:
        return ("", "", None, None, None, None)

    candidates = extract_candidate_sentences(cleaned_full_text)
    if not candidates:
        return (cleaned_full_text[:250], cleaned_full_text, None, None, 0, min(250, len(cleaned_full_text)))

    question_kw = extract_keywords(question)

    # Find answer sentences citing [ref]
    citing_sentences = []
    ref_marker = f"[{ref}]"
    for s_ans in re.split(r'(?<=[.!?])\s+|\n+', answer):
        if ref_marker in s_ans:
            citing_sentences.append(s_ans)

    if citing_sentences:
        answer_kw = extract_keywords(" ".join(citing_sentences))
    else:
        answer_kw = extract_keywords(answer)

    # Score each candidate sentence
    scored_candidates = []
    for idx, cand in enumerate(candidates):
        cand_kw = extract_keywords(cand)
        if not cand_kw:
            score = 0.0
        else:
            ans_overlap = len(cand_kw & answer_kw)
            q_overlap = len(cand_kw & question_kw)
            # Both question & answer matching weighted heavily
            score = (ans_overlap * 2.0) + (q_overlap * 1.0)
        scored_candidates.append((score, idx, cand))

    # Sort candidates by score descending
    scored_candidates.sort(key=lambda x: x[0], reverse=True)

    # Pick top 1-3 candidates with positive score
    top_picks = [item for item in scored_candidates[:max_sentences] if item[0] > 0]
    if not top_picks:
        # If no keywords matched, take the first 1-2 candidates
        top_picks = scored_candidates[:min(2, len(scored_candidates))]

    # Sort back by original sequence order in the passage
    top_picks.sort(key=lambda x: x[1])

    chosen_indices = [p[1] for p in top_picks]
    chosen_texts = [p[2] for p in top_picks]
    snippet = " ".join(chosen_texts)
    snippet = strip_bullets_and_quotes(snippet)

    # Context before: 1 candidate immediately before the first chosen sentence
    first_idx = chosen_indices[0]
    context_before = candidates[first_idx - 1] if first_idx > 0 else None

    # Context after: 1 candidate immediately after the last chosen sentence
    last_idx = chosen_indices[-1]
    context_after = candidates[last_idx + 1] if last_idx < len(candidates) - 1 else None

    # Determine character offsets in cleaned_full_text if present
    char_start = None
    char_end = None
    if chosen_texts:
        start_pos = cleaned_full_text.find(chosen_texts[0])
        if start_pos != -1:
            end_search = cleaned_full_text.find(chosen_texts[-1], start_pos)
            if end_search != -1:
                char_start = start_pos
                char_end = end_search + len(chosen_texts[-1])

    return (snippet, cleaned_full_text, context_before, context_after, char_start, char_end)


def extract_citation_refs(text: str) -> List[int]:
    """
    Extracts unique integer references from bracketed citation markers e.g. [1], [2][3].
    Returns sorted unique list of referenced integers.
    """
    matches = re.findall(r'\[(\d+)\]', text)
    refs = sorted(list(set(int(m) for m in matches)))
    return refs


def build_context_prompt(chunks: List[Dict[str, Any]]) -> str:
    """
    Formats retrieved chunks into numbered context passages.
    Passage [1] (Pages X-Y): ...
    """
    passages = []
    for idx, c in enumerate(chunks, start=1):
        p_start = c.get("page_start", 1)
        p_end = c.get("page_end", 1)
        content = c.get("content", "").strip()
        passages.append(f"Passage [{idx}] (Pages {p_start}-{p_end}):\n{content}")
    return "\n\n".join(passages)


def log_query_telemetry(
    user_id: str,
    document_id: str,
    question: str,
    retrieved_chunks: List[Dict[str, Any]],
    answer: str,
    latency_ms: int,
) -> None:
    """Records query metrics, retrieved chunk metadata, and latency into public.query_logs."""
    supabase = get_supabase_client()
    if not supabase:
        logger.warning("Supabase client not available for query logging.")
        return

    try:
        retrieved_summary = [
            {
                "chunk_id": c.get("id"),
                "similarity": c.get("similarity"),
                "page_start": c.get("page_start"),
                "page_end": c.get("page_end"),
            }
            for c in retrieved_chunks
        ]

        supabase.table("query_logs").insert({
            "user_id": user_id,
            "document_id": document_id,
            "question": question,
            "retrieved": retrieved_summary,
            "answer": answer,
            "latency_ms": latency_ms,
        }).execute()
        logger.info(f"Query logged successfully for doc {document_id} (latency: {latency_ms}ms).")
    except Exception as e:
        logger.warning(f"Failed to record query_log: {e}")


def execute_rag_query(
    document_id: str,
    question: str,
    user_id: str,
    top_k: int = settings.TOP_K,
    similarity_threshold: float = settings.SIMILARITY_THRESHOLD,
) -> ChatResponse:
    """
    Performs full RAG pipeline:
    1. Embed query (RETRIEVAL_QUERY)
    2. Vector search via match_chunks
    3. Similarity threshold check (returns NOT_FOUND_RESPONSE if below threshold)
    4. Gemini LLM generation with strict system prompt
    5. Citation extraction and validation
    6. Query logging
    """
    start_time = time.perf_counter()
    supabase = get_supabase_client()
    if not supabase:
        raise RuntimeError("Database connection not configured.")

    # 1. Embed Question
    query_vector = embedder_service.embed_query(question)

    # 2. Retrieve Matching Chunks
    rpc_res = supabase.rpc("match_chunks", {
        "query_embedding": query_vector,
        "match_document_id": document_id,
        "p_user_id": user_id,
        "match_count": top_k,
    }).execute()

    chunks = rpc_res.data or []
    best_similarity = max((float(c.get("similarity", 0.0)) for c in chunks), default=0.0)
    logger.info(f"Retrieved {len(chunks)} chunks for doc {document_id}. Best similarity: {best_similarity:.4f}")

    # 3. Threshold Check
    if not chunks or best_similarity < similarity_threshold:
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        log_query_telemetry(user_id, document_id, question, chunks, NOT_FOUND_RESPONSE, latency_ms)
        return ChatResponse(
            answer=NOT_FOUND_RESPONSE,
            citations=[],
            found=False
        )

    # 4. Build Context & Call Gemini
    context_text = build_context_prompt(chunks)
    full_prompt = f"Context Passages:\n\n{context_text}\n\nQuestion: {question}"

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.2,
    )

    try:
        response = call_gemini_generate_with_retry(
            client=client,
            model=settings.GEMINI_CHAT_MODEL,
            contents=full_prompt,
            config=config,
        )
    except Exception as e:
        err_str = str(e).lower()
        if "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI service is currently busy or quota is exhausted. Please try again in a few moments."
            )
        raise

    answer = response.text.strip() if response and response.text else NOT_FOUND_RESPONSE

    # 5. Parse Citations
    used_refs = extract_citation_refs(answer)
    citations: List[Citation] = []

    for ref in used_refs:
        # 1-based index matching Passage [1], Passage [2]...
        if 1 <= ref <= len(chunks):
            chunk = chunks[ref - 1]
            content = chunk.get("content", "")
            snippet, full_text_cleaned, context_before, context_after, char_start, char_end = (
                select_best_supporting_sentences(
                    chunk_text=content,
                    question=question,
                    answer=answer,
                    ref=ref,
                )
            )
            citations.append(Citation(
                ref=ref,
                chunk_id=str(chunk.get("id")),
                page_start=int(chunk.get("page_start", 1)),
                page_end=int(chunk.get("page_end", 1)),
                snippet=snippet,
                full_text=full_text_cleaned,
                similarity=float(chunk.get("similarity", 0.0)),
                char_start=char_start,
                char_end=char_end,
                context_before=context_before,
                context_after=context_after,
            ))

    # Detect if the model stated it could not find the answer in the document
    found = True
    lower_ans = answer.lower()
    if "could not find" in lower_ans or "couldn't find" in lower_ans or not citations:
        if not citations and ("not found" in lower_ans or "does not contain" in lower_ans):
            found = False

    latency_ms = int((time.perf_counter() - start_time) * 1000)

    # 6. Record telemetry
    log_query_telemetry(user_id, document_id, question, chunks, answer, latency_ms)

    return ChatResponse(
        answer=answer,
        citations=citations,
        found=found
    )

