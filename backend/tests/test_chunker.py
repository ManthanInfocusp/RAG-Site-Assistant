"""Smoke tests for the token-aware chunker."""

from __future__ import annotations

from app.rag.chunker import chunk_text


def test_chunker_returns_empty_for_empty_input():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_chunker_produces_sequential_ords():
    text = ("hello world " * 1000).strip()
    chunks = chunk_text(text, chunk_tokens=128, overlap_tokens=16)
    assert len(chunks) > 1
    assert [c.ord for c in chunks] == list(range(len(chunks)))


def test_chunker_overlap_keeps_information():
    text = ("alpha beta gamma delta " * 200).strip()
    chunks = chunk_text(text, chunk_tokens=64, overlap_tokens=16)
    # Consecutive chunks should share some overlapping tokens.
    assert any(chunks[i].text[-20:] in chunks[i + 1].text for i in range(len(chunks) - 1))
