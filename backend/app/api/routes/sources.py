from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.schemas import (
    DataSourceOut,
    PresignRequest,
    PresignResponse,
    UploadSourceCreate,
    UrlSourceCreate,
)
from app.core.deps import DB, CurrentUser
from app.models import DataSource, Site
from app.storage import presigned_put_url
from app.workers.tasks.ingest import ingest_data_source

router = APIRouter()


def _owned_site(db, user, site_id: str) -> Site:
    site = db.get(Site, site_id)
    if not site or site.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Site not found")
    return site


@router.get("/sites/{site_id}", response_model=list[DataSourceOut])
def list_sources(site_id: str, user: CurrentUser, db: DB):
    _owned_site(db, user, site_id)
    rows = db.scalars(
        select(DataSource)
        .where(DataSource.site_id == site_id)
        .order_by(DataSource.created_at.desc())
    ).all()
    return rows


@router.post(
    "/sites/{site_id}/url",
    response_model=DataSourceOut,
    status_code=status.HTTP_201_CREATED,
)
def create_url_source(site_id: str, payload: UrlSourceCreate, user: CurrentUser, db: DB):
    _owned_site(db, user, site_id)
    src = DataSource(
        site_id=site_id,
        type="url",
        config={
            "url": payload.url,
            "max_pages": payload.max_pages,
            "max_depth": payload.max_depth,
            "resync_interval_hours": payload.resync_interval_hours,
        },
        status="pending",
    )
    db.add(src)
    db.commit()
    db.refresh(src)
    ingest_data_source.delay(src.id)
    return src


@router.post(
    "/sites/{site_id}/upload",
    response_model=DataSourceOut,
    status_code=status.HTTP_201_CREATED,
)
def create_upload_source(
    site_id: str, payload: UploadSourceCreate, user: CurrentUser, db: DB
):
    _owned_site(db, user, site_id)
    if not payload.s3_keys:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No s3_keys provided")
    src = DataSource(
        site_id=site_id,
        type="upload",
        config={"s3_keys": payload.s3_keys, "original_names": payload.original_names},
        status="pending",
    )
    db.add(src)
    db.commit()
    db.refresh(src)
    ingest_data_source.delay(src.id)
    return src


@router.post("/sites/{site_id}/presign", response_model=PresignResponse)
def presign_upload(site_id: str, payload: PresignRequest, user: CurrentUser, db: DB):
    _owned_site(db, user, site_id)
    safe_name = payload.filename.replace("/", "_").replace("\\", "_")
    key = f"uploads/{site_id}/{uuid.uuid4()}/{safe_name}"
    url = presigned_put_url(key, payload.content_type)
    return PresignResponse(upload_url=url, s3_key=key, expires_in=600)


@router.get("/{source_id}", response_model=DataSourceOut)
def get_source(source_id: str, user: CurrentUser, db: DB):
    src = db.get(DataSource, source_id)
    if not src:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Source not found")
    _owned_site(db, user, src.site_id)
    return src


@router.post("/{source_id}/resync", response_model=DataSourceOut)
def resync_source(source_id: str, user: CurrentUser, db: DB):
    src = db.get(DataSource, source_id)
    if not src:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Source not found")
    _owned_site(db, user, src.site_id)
    src.status = "pending"
    src.error_message = None
    db.commit()
    ingest_data_source.delay(src.id)
    db.refresh(src)
    return src


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(source_id: str, user: CurrentUser, db: DB):
    src = db.get(DataSource, source_id)
    if not src:
        return
    _owned_site(db, user, src.site_id)
    db.delete(src)
    db.commit()
