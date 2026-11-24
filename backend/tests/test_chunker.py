"""
Unit tests for page-aware chunker (backend/app/services/chunker.py).
Tests overlap, page range accuracy, boundary preservation, and no empty chunks.
"""

import pytest
from app.services.chunker import chunk_pages, clean_text, PageText


def test_clean_text_hyphenation_and_whitespace():
    raw = "This is a demon-\nstration of hyphen-\n  ated line breaks and    multiple   spaces.\n\n\n\nNew paragraph."
    cleaned = clean_text(raw)
    assert "demonstration" in cleaned
    assert "hyphenated" in cleaned
    assert "   " not in cleaned
    assert "\n\n\n" not in cleaned
    assert "New paragraph." in cleaned


def test_no_empty_chunks():
    pages = [
        PageText(page_number=1, text="   "),
        PageText(page_number=2, text="\n\n\t  \n"),
        PageText(page_number=3, text="Actual content on page 3."),
    ]
    chunks = chunk_pages(pages, chunk_size_tokens=100, chunk_overlap_tokens=15)
    assert len(chunks) == 1
    assert chunks[0].content == "Actual content on page 3."
    assert chunks[0].page_start == 3
    assert chunks[0].page_end == 3
    assert len(chunks[0].content.strip()) > 0


def test_page_ranges_correct():
    # Page 1 has short text; Page 2 has short text. Together they should form 1 chunk spanning pages 1-2
    pages = [
        PageText(page_number=1, text="First page content discussing introduction to machine learning."),
        PageText(page_number=2, text="Second page content expanding into deep neural networks."),
    ]
    # Set chunk size large enough to hold both
    chunks = chunk_pages(pages, chunk_size_tokens=200, chunk_overlap_tokens=20)
    assert len(chunks) == 1
    assert chunks[0].page_start == 1
    assert chunks[0].page_end == 2
    assert "First page content" in chunks[0].content
    assert "Second page content" in chunks[0].content


def test_chunk_overlap_works():
    # Create several paragraphs across 3 pages to force multiple chunks
    para1 = "Paragraph 1: Deep learning is a subset of machine learning based on artificial neural networks. " * 3
    para2 = "Paragraph 2: Representation learning enables a system to automatically discover representations. " * 3
    para3 = "Paragraph 3: Convolutional neural networks excel in visual imagery analysis and object recognition. " * 3
    para4 = "Paragraph 4: Recurrent neural networks process sequential data such as natural language and speech. " * 3

    pages = [
        PageText(page_number=1, text=f"{para1}\n\n{para2}"),
        PageText(page_number=2, text=f"{para3}\n\n{para4}"),
    ]

    # Use smaller chunk size (~100 tokens = ~400 chars, overlap 25 tokens = ~100 chars)
    chunks = chunk_pages(pages, chunk_size_tokens=100, chunk_overlap_tokens=25)
    assert len(chunks) >= 2, "Expected multiple chunks to test overlap"

    # Verify all chunks have non-empty content and valid indices
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i
        assert len(chunk.content.strip()) > 0
        assert chunk.page_start <= chunk.page_end
        assert chunk.token_estimate > 0

    # Test overlap between chunk 0 and chunk 1
    chunk0_words = set(chunks[0].content.split()[-10:])  # last 10 words of chunk 0
    chunk1_words = set(chunks[1].content.split()[:25])   # first 25 words of chunk 1
    common_words = chunk0_words.intersection(chunk1_words)
    assert len(common_words) > 0, "Expected overlapping words between consecutive chunks"


def test_never_cuts_mid_sentence_when_possible():
    s1 = "This is the first sentence about architecture."
    s2 = "This is the second sentence about design patterns."
    s3 = "This is the third sentence explaining domain driven development."

    pages = [PageText(page_number=1, text=f"{s1} {s2}\n\n{s3}")]
    # Set chunk size small so s3 goes to chunk 2
    chunks = chunk_pages(pages, chunk_size_tokens=30, chunk_overlap_tokens=0)
    for c in chunks:
        # Verify that sentences are not abruptly truncated
        assert c.content.endswith(".") or c.content.endswith("!") or c.content.endswith("?")


def test_empty_document():
    pages = []
    chunks = chunk_pages(pages)
    assert chunks == []

