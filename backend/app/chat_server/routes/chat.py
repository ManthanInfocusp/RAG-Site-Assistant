"""SSE chat endpoint.

Auth: visitor-anonymous. We validate the `site_key` against `Site.public_key`
and the request `Origin` against the site's domain allowlist.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select

from app.chat_server.pipeline import stream_answer
from app.chat_server.rate_limit import check_and_increment
from app.core.deps import DB
from app.models import Conversation, Site

router = APIRouter()


class ChatRequest(BaseModel):
    site_key: str
    message: str
    conversation_id: str | None = None
    visitor_id: str | None = None
    visitor_identifier: str | None = None


def _sse_event(event: str, data: str) -> bytes:
    # Encode multi-line data correctly per SSE spec.
    lines = data.splitlines() or [""]
    payload = "".join(f"data: {line}\n" for line in lines)
    return f"event: {event}\n{payload}\n".encode()


@router.post("/stream")
def chat_stream(payload: ChatRequest, request: Request, db: DB):
    origin = request.headers.get("origin") or request.headers.get("referer")
    client_ip = request.client.host if request.client else "unknown"

    site = db.scalar(select(Site).where(Site.public_key == payload.site_key))
    if not site:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid site key")

    if site.allowed_origins:
        normalized = (origin or "").rstrip("/")
        allowed = {o.strip().rstrip("/") for o in site.allowed_origins.split(",") if o.strip()}
        if normalized not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Origin not allowed for this site")

    if not check_and_increment(payload.site_key, client_ip):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Rate limit exceeded")

    # Resolve or create conversation.
    if payload.conversation_id:
        convo = db.get(Conversation, payload.conversation_id)
        if not convo or convo.site_id != site.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    else:
        convo = Conversation(
            site_id=site.id,
            visitor_id=payload.visitor_id,
            visitor_identifier=payload.visitor_identifier,
        )
        db.add(convo)
        db.commit()
        db.refresh(convo)

    conversation_id = convo.id

    def event_stream() -> Iterator[bytes]:
        # First event so the client immediately learns the conversation id.
        yield _sse_event("ready", json.dumps({"conversation_id": conversation_id}))
        try:
            for event, data in stream_answer(
                db,
                site_id=site.id,
                conversation_id=conversation_id,
                user_text=payload.message,
            ):
                yield _sse_event(event, data)
        except Exception as exc:  # noqa: BLE001
            yield _sse_event("error", json.dumps({"message": str(exc)}))

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
