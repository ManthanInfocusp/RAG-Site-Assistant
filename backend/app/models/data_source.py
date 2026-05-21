from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models._base import TimestampMixin, new_uuid


class DataSource(Base, TimestampMixin):
    """A configured ingestion source for a site (URL crawl or uploaded files)."""

    __tablename__ = "data_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    site_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sites.id", ondelete="CASCADE"), index=True, nullable=False
    )
    type: Mapped[str] = mapped_column(String(16), nullable=False)  # "url" | "upload"
    # url: {"url": "...", "max_pages": int, "max_depth": int}
    # upload: {"s3_keys": ["..."], "original_names": ["..."]}
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    # "pending" | "running" | "ready" | "failed"
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    stats: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # {"pages": int, "documents": int, "chunks": int}

    site: Mapped["Site"] = relationship("Site", back_populates="data_sources")  # noqa: F821
    documents: Mapped[list["Document"]] = relationship(  # noqa: F821
        "Document", back_populates="data_source", cascade="all, delete-orphan"
    )
