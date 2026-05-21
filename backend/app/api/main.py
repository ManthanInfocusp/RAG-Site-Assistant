"""FastAPI app for the REST API service (portal-facing).

Endpoints:
  /v1/auth/*       - login / logout / me
  /v1/sites/*      - CRUD on sites
  /v1/sources/*    - data sources (URL crawl, upload)
  /v1/conversations - chat history for owner
  /v1/widget/config - public config endpoint used by the embed widget
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, conversations, sites, sources, widget
from app.core import metrics
from app.core.config import settings
from app.core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    get_logger("api").info("api.start", env=settings.env)
    yield


app = FastAPI(title="RAG Site Assistant API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "api"}


metrics.install(app)

app.include_router(auth.router, prefix="/v1/auth", tags=["auth"])
app.include_router(sites.router, prefix="/v1/sites", tags=["sites"])
app.include_router(sources.router, prefix="/v1/sources", tags=["sources"])
app.include_router(conversations.router, prefix="/v1/conversations", tags=["conversations"])
app.include_router(widget.router, prefix="/v1/widget", tags=["widget"])
