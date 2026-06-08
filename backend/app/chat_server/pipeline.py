"""End-to-end RAG query pipeline used by the chat-server SSE endpoint."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Conversation, Message, Site
from app.rag.embedder import get_embedder
from app.rag.llm_client import get_llm_client
from app.rag.prompts import PromptMessage, build_messages
from app.rag.retriever import SiteScopedRetriever


@dataclass
class StreamResult:
    answer: str
    citations: list[dict]


def _load_history(db: Session, conversation_id: str) -> list[PromptMessage]:
    convo = db.get(Conversation, conversation_id)
    if not convo:
        return []
    # Last N turns (user+assistant pairs), in chronological order.
    msgs = convo.messages[-(settings.chat_history_turns * 2) :]
    return [PromptMessage(role=m.role, content=m.content) for m in msgs]


def stream_answer(
    db: Session,
    *,
    site_id: str,
    conversation_id: str,
    user_text: str,
) -> Iterator[tuple[str, str]]:
    """Yield (event, data) tuples for SSE.

    Events:
      - "citations": initial JSON payload of citations
      - "delta": each streamed token (str)
      - "done": final JSON payload with conversation_id
    """
    embedder = get_embedder()
    llm = get_llm_client()

    history = _load_history(db, conversation_id)

    site = db.get(Site, site_id)
    custom_system_prompt = site.system_prompt if site else None

    # Embed the user query.
    [query_vec] = embedder.embed([user_text])

    # Retrieve site-scoped chunks and discard irrelevant ones.
    retriever = SiteScopedRetriever(db, site_id)
    all_chunks = retriever.search(query_vec, k=settings.chat_max_context_chunks)
    chunks = [c for c in all_chunks if c.distance <= settings.chat_context_distance_threshold]

    # Persist the user message immediately so a refresh shows it.
    user_msg = Message(conversation_id=conversation_id, role="user", content=user_text)
    db.add(user_msg)
    db.commit()

    # No relevant context found — return a canned response without calling the LLM.
    if not chunks:
        fallback = "I don't have information about that in this site's knowledge base."
        yield ("citations", "[]")
        yield ("delta", fallback)
        db.add(Message(conversation_id=conversation_id, role="assistant", content=fallback, citations=[]))
        db.commit()
        yield ("done", _json_safe({"conversation_id": conversation_id}))
        return

    messages, citations = build_messages(user_text, chunks, history, custom_system_prompt=custom_system_prompt)

    yield ("citations", _json_safe(citations))

    answer_chunks: list[str] = []
    for delta in llm.stream(messages):
        answer_chunks.append(delta)
        yield ("delta", delta)

    answer = "".join(answer_chunks)

    db.add(Message(
        conversation_id=conversation_id,
        role="assistant",
        content=answer,
        citations=citations,
    ))
    db.commit()

    yield ("done", _json_safe({"conversation_id": conversation_id}))


def _json_safe(value) -> str:
    import json

    return json.dumps(value, default=str)
