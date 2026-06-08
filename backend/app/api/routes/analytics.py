from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select, text

from app.api.schemas import AnalyticsOut, DailyCount, TopSource
from app.core.deps import DB, CurrentUser
from app.models import Conversation, Message, Site

router = APIRouter()


@router.get("/sites/{site_id}", response_model=AnalyticsOut)
def get_analytics(site_id: str, user: CurrentUser, db: DB):
    site = db.get(Site, site_id)
    if not site or site.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Site not found")

    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    total_conversations: int = db.scalar(
        select(func.count(Conversation.id)).where(Conversation.site_id == site_id)
    ) or 0

    total_messages: int = db.scalar(
        select(func.count(Message.id))
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(Conversation.site_id == site_id)
    ) or 0

    conversations_today: int = db.scalar(
        select(func.count(Conversation.id)).where(
            Conversation.site_id == site_id,
            Conversation.created_at >= today_start,
        )
    ) or 0

    conversations_last_7d: int = db.scalar(
        select(func.count(Conversation.id)).where(
            Conversation.site_id == site_id,
            Conversation.created_at >= seven_days_ago,
        )
    ) or 0

    # Conversations per day for last 30 days
    daily_rows = db.execute(
        text("""
            SELECT DATE(c.created_at AT TIME ZONE 'UTC') AS day, COUNT(*) AS cnt
            FROM conversations c
            WHERE c.site_id = :site_id AND c.created_at >= :since
            GROUP BY day
            ORDER BY day
        """),
        {"site_id": site_id, "since": thirty_days_ago},
    ).fetchall()
    daily_conversations = [DailyCount(date=str(r.day), count=r.cnt) for r in daily_rows]

    # Top cited sources (unnest JSONB citations array)
    source_rows = db.execute(
        text("""
            SELECT
                citation->>'source_uri' AS source_uri,
                citation->>'title'      AS title,
                COUNT(*)                AS citation_count
            FROM messages m
            JOIN conversations c ON c.id = m.conversation_id,
            LATERAL jsonb_array_elements(m.citations) AS citation
            WHERE c.site_id = :site_id AND m.role = 'assistant'
              AND jsonb_array_length(m.citations) > 0
            GROUP BY source_uri, title
            ORDER BY citation_count DESC
            LIMIT 10
        """),
        {"site_id": site_id},
    ).fetchall()
    top_sources = [
        TopSource(source_uri=r.source_uri or "", title=r.title, citation_count=r.citation_count)
        for r in source_rows
        if r.source_uri
    ]

    # Most recent user questions
    question_rows = db.scalars(
        select(Message.content)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(Conversation.site_id == site_id, Message.role == "user")
        .order_by(Message.created_at.desc())
        .limit(20)
    ).all()

    return AnalyticsOut(
        total_conversations=total_conversations,
        total_messages=total_messages,
        conversations_today=conversations_today,
        conversations_last_7d=conversations_last_7d,
        daily_conversations=daily_conversations,
        top_sources=top_sources,
        recent_questions=list(question_rows),
    )
