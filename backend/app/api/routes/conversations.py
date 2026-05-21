from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.schemas import ConversationOut
from app.core.deps import DB, CurrentUser
from app.models import Conversation, Site

router = APIRouter()


@router.get("/sites/{site_id}", response_model=list[ConversationOut])
def list_conversations(site_id: str, user: CurrentUser, db: DB, limit: int = 50):
    site = db.get(Site, site_id)
    if not site or site.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Site not found")
    rows = db.scalars(
        select(Conversation)
        .where(Conversation.site_id == site_id)
        .order_by(Conversation.created_at.desc())
        .limit(limit)
    ).all()
    return rows


@router.get("/{conversation_id}", response_model=ConversationOut)
def get_conversation(conversation_id: str, user: CurrentUser, db: DB):
    convo = db.get(Conversation, conversation_id)
    if not convo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    site = db.get(Site, convo.site_id)
    if not site or site.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    return convo
