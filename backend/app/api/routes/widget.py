"""Public endpoint consumed by the embed widget for initial config."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.schemas import WidgetConfigOut
from app.core.deps import DB
from app.models import Site

router = APIRouter()


@router.get("/config", response_model=WidgetConfigOut)
def widget_config(db: DB, key: str = Query(..., min_length=8)):
    site = db.scalar(select(Site).where(Site.public_key == key))
    if not site:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown site key")
    return WidgetConfigOut(
        site_id=site.id,
        name=site.name,
        widget_config=site.widget_config or {},
        allowed_origins=[o.strip() for o in site.allowed_origins.split(",") if o.strip()],
    )
