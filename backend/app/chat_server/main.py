"""FastAPI app for the chat / SSE server (visitor-facing)."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.chat_server.routes import chat
from app.core import metrics
from app.core.config import settings
from app.core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    get_logger("chat-server").info("chat.start", env=settings.env)
    yield


app = FastAPI(title="RAG Site Assistant Chat", version="0.1.0", lifespan=lifespan)

# Widget can be embedded on any origin; per-site allowlist is enforced inside
# the streaming endpoint, not via CORS. We still need to echo the Origin header
# back so browsers accept the response on cross-origin XHR/fetch.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "chat-server"}


metrics.install(app)

app.include_router(chat.router, prefix="/v1/chat", tags=["chat"])
