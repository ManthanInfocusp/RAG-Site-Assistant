"""Prompt construction for the RAG chat."""

from __future__ import annotations

from dataclasses import dataclass

from app.rag.retriever import RetrievedChunk

SYSTEM_PROMPT = """You are a strict site assistant. Follow these rules without exception:

1. Your ONLY source of information is the CONTEXT block in the user message. \
You are PROHIBITED from using your training data or general knowledge under any circumstances.
2. If the CONTEXT directly answers the question, reply concisely and cite sources \
inline as [1], [2], etc. matching the numbered context items.
3. If the CONTEXT does not directly answer the question — even partially, even if \
you know the answer from training — reply with EXACTLY this sentence and nothing else: \
"I don't have information about that in this site's knowledge base."
4. Never guess, extrapolate, or say things like "generally speaking" or \
"based on common knowledge".
5. The CONTEXT being about a related topic does NOT mean it answers the question. \
Apply rule 3 unless the answer is explicitly stated in the CONTEXT."""


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
    custom_system_prompt: str | None = None,
) -> tuple[list[PromptMessage], list[dict]]:
    context_text, citations = build_context_block(chunks)
    system_content = custom_system_prompt.strip() if custom_system_prompt and custom_system_prompt.strip() else SYSTEM_PROMPT
    msgs: list[PromptMessage] = [PromptMessage(role="system", content=system_content)]
    if history:
        msgs.extend(history)
    msgs.append(
        PromptMessage(
            role="user",
            content=(
                f"CONTEXT:\n{context_text}\n\n"
                f"QUESTION: {user_query}\n\n"
                "REMINDER: Answer ONLY if the CONTEXT above directly contains the answer. "
                "If it does not, reply with exactly: "
                "\"I don't have information about that in this site's knowledge base.\""
            ),
        )
    )
    return msgs, citations
