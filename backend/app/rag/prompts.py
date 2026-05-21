"""Prompt construction for the RAG chat."""

from __future__ import annotations

from dataclasses import dataclass

from app.rag.retriever import RetrievedChunk

SYSTEM_PROMPT = """You are a helpful site assistant. Answer the user's question \
strictly using the provided CONTEXT. If the answer is not contained in the \
context, say you don't have that information and suggest where they could look \
on the site instead. Be concise. Cite sources inline as [1], [2], etc. matching \
the numbered context items. Never invent facts."""


@dataclass
class PromptMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


def build_context_block(chunks: list[RetrievedChunk]) -> tuple[str, list[dict]]:
    """Return (context_text, citations) where citations is JSON-serialisable."""
    lines: list[str] = []
    citations: list[dict] = []
    for i, ch in enumerate(chunks, start=1):
        title = ch.title or ch.source_uri
        lines.append(f"[{i}] {title}\n{ch.content}")
        citations.append(
            {
                "index": i,
                "chunk_id": ch.chunk_id,
                "document_id": ch.document_id,
                "source_uri": ch.source_uri,
                "title": ch.title,
            }
        )
    return "\n\n".join(lines), citations


def build_messages(
    user_query: str,
    chunks: list[RetrievedChunk],
    history: list[PromptMessage] | None = None,
) -> tuple[list[PromptMessage], list[dict]]:
    context_text, citations = build_context_block(chunks)
    msgs: list[PromptMessage] = [PromptMessage(role="system", content=SYSTEM_PROMPT)]
    if history:
        msgs.extend(history)
    msgs.append(
        PromptMessage(
            role="user",
            content=f"CONTEXT:\n{context_text}\n\nQUESTION: {user_query}",
        )
    )
    return msgs, citations
