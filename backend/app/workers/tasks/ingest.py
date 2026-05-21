"""Orchestrating Celery task: takes a DataSource id and ingests it end-to-end."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.db import SessionLocal
from app.core.logging import get_logger
from app.models import Chunk, DataSource, Document
from app.rag.chunker import chunk_text
from app.rag.embedder import get_embedder
from app.storage import get_object_bytes
from app.workers.celery_app import celery_app
from app.workers.tasks.crawl import crawl_site
from app.workers.tasks.parse import parse_bytes_by_filename

log = get_logger("ingest")


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@celery_app.task(name="ingest_data_source", bind=True, max_retries=2)
def ingest_data_source(self, data_source_id: str) -> dict:
    db = SessionLocal()
    try:
        src = db.get(DataSource, data_source_id)
        if not src:
            log.warning("ingest.missing_source", id=data_source_id)
            return {"status": "missing"}

        src.status = "running"
        src.error_message = None
        db.commit()

        try:
            if src.type == "url":
                stats = _ingest_url(db, src)
            elif src.type == "upload":
                stats = _ingest_upload(db, src)
            else:
                raise ValueError(f"Unknown source type: {src.type}")
        except Exception as exc:  # noqa: BLE001
            log.exception("ingest.failed", id=data_source_id)
            src.status = "failed"
            src.error_message = str(exc)[:1900]
            db.commit()
            raise

        src.status = "ready"
        src.stats = stats
        src.last_synced_at = datetime.now(timezone.utc)
        db.commit()
        return {"status": "ready", **stats}
    finally:
        db.close()


def _ingest_url(db, src: DataSource) -> dict:
    cfg = src.config or {}
    pages = crawl_site(
        cfg["url"],
        max_pages=cfg.get("max_pages"),
        max_depth=cfg.get("max_depth"),
    )
    n_docs = 0
    n_chunks = 0
    for page in pages:
        content_hash = _hash_text(page.text)
        existing = db.scalar(
            select(Document).where(
                Document.site_id == src.site_id,
                Document.source_uri == page.url,
            )
        )
        if existing and existing.content_hash == content_hash:
            continue
        if existing:
            db.delete(existing)
            db.flush()

        doc = Document(
            site_id=src.site_id,
            data_source_id=src.id,
            source_uri=page.url,
            title=page.title,
            content_hash=content_hash,
            raw_text=page.text,
            status="ready",
        )
        db.add(doc)
        db.flush()
        n_chunks += _embed_and_store(db, doc)
        n_docs += 1
    db.commit()
    return {"pages": len(pages), "documents": n_docs, "chunks": n_chunks}


def _ingest_upload(db, src: DataSource) -> dict:
    cfg = src.config or {}
    keys: list[str] = cfg.get("s3_keys") or []
    names: list[str] = cfg.get("original_names") or keys
    n_docs = 0
    n_chunks = 0
    for key, name in zip(keys, names, strict=False):
        data = get_object_bytes(key)
        text = parse_bytes_by_filename(name, data)
        if not text.strip():
            continue
        content_hash = _hash_text(text)
        doc = Document(
            site_id=src.site_id,
            data_source_id=src.id,
            source_uri=f"s3://{key}",
            title=name,
            content_hash=content_hash,
            raw_text=text,
            status="ready",
        )
        db.add(doc)
        db.flush()
        n_chunks += _embed_and_store(db, doc)
        n_docs += 1
    db.commit()
    return {"files": len(keys), "documents": n_docs, "chunks": n_chunks}


def _embed_and_store(db, doc: Document) -> int:
    chunks = chunk_text(doc.raw_text or "")
    if not chunks:
        return 0
    embedder = get_embedder()
    texts = [c.text for c in chunks]
    vectors = embedder.embed(texts)
    for c, vec in zip(chunks, vectors, strict=True):
        db.add(
            Chunk(
                site_id=doc.site_id,
                document_id=doc.id,
                ord=c.ord,
                content=c.text,
                embedding=vec,
                chunk_metadata={"source_uri": doc.source_uri, "title": doc.title},
            )
        )
    db.flush()
    return len(chunks)
