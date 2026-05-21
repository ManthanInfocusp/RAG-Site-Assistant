from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.security import generate_public_key, generate_secret_key
from app.models._base import TimestampMixin, new_uuid


class Site(Base, TimestampMixin):
    __tablename__ = "sites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Comma-separated list of allowed origins (e.g. "https://example.com,https://www.example.com")
    allowed_origins: Mapped[str] = mapped_column(String(2048), nullable=False, default="")
    public_key: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False, default=generate_public_key
    )
    secret_key: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, default=generate_secret_key
    )
    # Theme + welcome message + persona configurable per site
    widget_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    owner: Mapped["User"] = relationship("User", back_populates="sites")  # noqa: F821
    data_sources: Mapped[list["DataSource"]] = relationship(  # noqa: F821
        "DataSource", back_populates="site", cascade="all, delete-orphan"
    )

    def origin_allowed(self, origin: str | None) -> bool:
        if not origin:
            return False
        allowed = {o.strip() for o in self.allowed_origins.split(",") if o.strip()}
        return origin in allowed
