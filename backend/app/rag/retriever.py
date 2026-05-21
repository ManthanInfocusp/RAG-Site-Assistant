"""Site-scoped vector retrieval.

Every read goes through this class, which forces a `site_id` filter on every
`chunks` query. No caller is allowed to write raw SQL against `chunks`.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Chunk, Document


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    content: str
    source_uri: str
    title: str | None
    distance: float


class SiteScopedRetriever:
    def __init__(self, db: Session, site_id: str) -> None:
        if not site_id:
            raise ValueError("site_id is required")
        self._db = db
        self._site_id = site_id

    def search(self, query_embedding: list[float], k: int = 6) -> list[RetrievedChunk]:
        stmt = (
            select(
                Chunk.id,
                Chunk.document_id,
                Chunk.content,
                Document.source_uri,
                Document.title,
                Chunk.embedding.cosine_distance(query_embedding).label("distance"),
            )
            .join(Document, Document.id == Chunk.document_id)
            .where(Chunk.site_id == self._site_id)
            .order_by("distance")
            .limit(k)
        )
        rows = self._db.execute(stmt).all()
        return [
            RetrievedChunk(
                chunk_id=r.id,
                document_id=r.document_id,
                content=r.content,
                source_uri=r.source_uri,
                title=r.title,
                distance=float(r.distance),
            )
            for r in rows
        ]
