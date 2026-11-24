"""
Page-aware text chunker for RAG ingestion.
Splits text on paragraph boundaries first, then sentence boundaries.
Tracks page_start and page_end per chunk and supports configurable overlap.
"""

import re
from typing import List, NamedTuple
from app.core.config import settings


class PageText(NamedTuple):
    page_number: int
    text: str


class TextChunk(NamedTuple):
    chunk_index: int
    content: str
    page_start: int
    page_end: int
    token_estimate: int


class TextSegment(NamedTuple):
    text: str
    page: int


def clean_text(raw_text: str) -> str:
    """
    Cleans raw extracted page text:
    - Fixes hyphenated line breaks (e.g. 'infor-\nmation' -> 'information')
    - Collapses repeated horizontal spaces/tabs to a single space
    - Normalizes newlines: collapses 3+ newlines to 2 newlines (paragraphs)
    - Strips leading and trailing whitespace
    """
    if not raw_text:
        return ""

    # Fix hyphenated words broken across lines: e.g. "connec-\ntion" -> "connection"
    # Matches a lowercase word fragment, hyphen, newline, and next lowercase word fragment
    cleaned = re.sub(r'(\b[a-zA-Z]+)-\s*\n\s*([a-zA-Z]+\b)', r'\1\2', raw_text)

    # Collapse repeated horizontal whitespace (spaces, tabs)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)

    # Normalize excessive consecutive newlines to maximum two newlines
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    return cleaned.strip()


def _split_into_sentences(text: str) -> List[str]:
    """Splits a paragraph into sentences preserving ending punctuation."""
    # Split on whitespace following period, exclamation mark, or question mark
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def _split_page_into_segments(page: PageText, max_segment_chars: int) -> List[TextSegment]:
    """
    Breaks a single page's text into small semantic segments (paragraphs or sentences)
    each tagged with the source page number.
    """
    segments: List[TextSegment] = []
    paragraphs = page.text.split("\n\n")

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(para) <= max_segment_chars:
            segments.append(TextSegment(text=para, page=page.page_number))
        else:
            # Paragraph is too long; break into sentences
            sentences = _split_into_sentences(para)
            for sentence in sentences:
                if len(sentence) <= max_segment_chars:
                    segments.append(TextSegment(text=sentence, page=page.page_number))
                else:
                    # Rare edge case: single sentence exceeds max segment chars.
                    # Split on word boundaries.
                    words = sentence.split(" ")
                    current_sub = []
                    current_len = 0
                    for word in words:
                        if current_len + len(word) + 1 > max_segment_chars and current_sub:
                            segments.append(TextSegment(text=" ".join(current_sub), page=page.page_number))
                            current_sub = [word]
                            current_len = len(word)
                        else:
                            current_sub.append(word)
                            current_len += len(word) + 1
                    if current_sub:
                        segments.append(TextSegment(text=" ".join(current_sub), page=page.page_number))

    return segments


def chunk_pages(
    pages: List[PageText],
    chunk_size_tokens: int = settings.CHUNK_SIZE_TOKENS,
    chunk_overlap_tokens: int = settings.CHUNK_OVERLAP_TOKENS,
) -> List[TextChunk]:
    """
    Takes an ordered list of PageText items and produces page-aware chunks.
    
    1 token ≈ 4 characters.
    Chunk size in characters ≈ chunk_size_tokens * 4.
    Overlap in characters ≈ chunk_overlap_tokens * 4.
    """
    max_chunk_chars = max(chunk_size_tokens * 4, 200)
    overlap_chars = max(chunk_overlap_tokens * 4, 0)

    # 1. Collect all atomic segments across all pages
    all_segments: List[TextSegment] = []
    for page in pages:
        cleaned = clean_text(page.text)
        if cleaned:
            page_segments = _split_page_into_segments(
                PageText(page_number=page.page_number, text=cleaned),
                max_segment_chars=max_chunk_chars
            )
            all_segments.extend(page_segments)

    if not all_segments:
        return []

    chunks: List[TextChunk] = []
    chunk_idx = 0
    seg_idx = 0
    total_segments = len(all_segments)

    while seg_idx < total_segments:
        current_chunk_segments: List[TextSegment] = []
        current_char_count = 0
        end_idx = seg_idx

        # Accumulate segments until reaching chunk target
        while end_idx < total_segments:
            seg = all_segments[end_idx]
            seg_len = len(seg.text)
            separator_len = 2 if current_chunk_segments else 0  # "\n\n" between paragraphs

            if current_char_count + separator_len + seg_len > max_chunk_chars and current_chunk_segments:
                # Adding this segment would exceed target size; finish current chunk
                break

            current_chunk_segments.append(seg)
            current_char_count += separator_len + seg_len
            end_idx += 1

        if not current_chunk_segments:
            # Safety fallback for single segment exceeding max_chunk_chars
            current_chunk_segments.append(all_segments[end_idx])
            end_idx += 1

        # Join content
        chunk_content = "\n\n".join(s.text for s in current_chunk_segments).strip()
        page_start = min(s.page for s in current_chunk_segments)
        page_end = max(s.page for s in current_chunk_segments)
        # Token estimate: 1 token ≈ 4 characters (standard approximation)
        token_estimate = max(1, len(chunk_content) // 4)

        chunks.append(TextChunk(
            chunk_index=chunk_idx,
            content=chunk_content,
            page_start=page_start,
            page_end=page_end,
            token_estimate=token_estimate
        ))
        chunk_idx += 1

        # If we reached the end of all segments, stop
        if end_idx >= total_segments:
            break

        # Calculate overlap for the next chunk
        # Look backwards from end_idx to pick up segments for overlap
        if overlap_chars > 0:
            accumulated_overlap = 0
            overlap_start_idx = end_idx
            for i in range(end_idx - 1, seg_idx - 1, -1):
                seg_len = len(all_segments[i].text)
                if accumulated_overlap + seg_len <= overlap_chars:
                    accumulated_overlap += seg_len
                    overlap_start_idx = i
                else:
                    break

            # Guarantee forward progress: overlap_start_idx must be > seg_idx
            if overlap_start_idx <= seg_idx:
                # If overlap didn't advance, advance at least by 1 segment
                seg_idx = seg_idx + 1
            else:
                seg_idx = overlap_start_idx
        else:
            seg_idx = end_idx

    return chunks

