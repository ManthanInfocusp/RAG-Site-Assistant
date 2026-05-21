from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.schemas import SiteCreate, SiteOut, SiteUpdate
from app.core.deps import DB, CurrentUser
from app.core.security import generate_public_key, generate_secret_key
from app.models import Site

router = APIRouter()


def _get_owned_site(db, user, site_id: str) -> Site:
    site = db.get(Site, site_id)
    if not site or site.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Site not found")
    return site


@router.get("", response_model=list[SiteOut])
def list_sites(user: CurrentUser, db: DB):
    rows = db.scalars(
        select(Site).where(Site.owner_id == user.id).order_by(Site.created_at.desc())
    ).all()
    return rows


@router.post("", response_model=SiteOut, status_code=status.HTTP_201_CREATED)
def create_site(payload: SiteCreate, user: CurrentUser, db: DB):
    site = Site(
        owner_id=user.id,
        name=payload.name,
        allowed_origins=payload.allowed_origins,
        widget_config=payload.widget_config or {},
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


@router.get("/{site_id}", response_model=SiteOut)
def get_site(site_id: str, user: CurrentUser, db: DB):
    return _get_owned_site(db, user, site_id)


@router.patch("/{site_id}", response_model=SiteOut)
def update_site(site_id: str, payload: SiteUpdate, user: CurrentUser, db: DB):
    site = _get_owned_site(db, user, site_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(site, field, value)
    db.commit()
    db.refresh(site)
    return site


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_site(site_id: str, user: CurrentUser, db: DB):
    site = _get_owned_site(db, user, site_id)
    db.delete(site)
    db.commit()


@router.post("/{site_id}/rotate-keys", response_model=SiteOut)
def rotate_keys(site_id: str, user: CurrentUser, db: DB):
    """Rotate both the public (widget) key and the secret key.

    The old public_key stops working immediately; the embed snippet must be
    updated on the host site.
    """
    site = _get_owned_site(db, user, site_id)
    site.public_key = generate_public_key()
    site.secret_key = generate_secret_key()
    db.commit()
    db.refresh(site)
    return site
