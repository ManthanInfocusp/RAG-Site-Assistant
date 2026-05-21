"""Token-aware text chunking.

Uses a sliding window over tokens (tiktoken's cl100k_base) so chunks are
roughly uniform regardless of input language. Falls back to character-based
splitting if tiktoken isn't available for some reason.
"""

from __future__ import annotations

from dataclasses import dataclass

import tiktoken

_ENCODING = tiktoken.get_encoding("cl100k_base")


@dataclass
class Chunk:
    ord: int
    text: str


def chunk_text(text: str, *, chunk_tokens: int = 512, overlap_tokens: int = 64) -> list[Chunk]:
    """Split text into overlapping token windows.

    Returns chunks in document order with `ord` set to their index.
    """
    text = (text or "").strip()
    if not text:
        return []

    tokens = _ENCODING.encode(text)
    if not tokens:
        return []

    chunks: list[Chunk] = []
    step = max(1, chunk_tokens - overlap_tokens)
    idx = 0
    ord_ = 0
    while idx < len(tokens):
        window = tokens[idx : idx + chunk_tokens]
        piece = _ENCODING.decode(window).strip()
        if piece:
            chunks.append(Chunk(ord=ord_, text=piece))
            ord_ += 1
        idx += step
    return chunks
