"""Pydantic request/response schemas used across REST routes."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

# --- Auth -----------------------------------------------------------------

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    name: str | None

    class Config:
        from_attributes = True


# --- Sites ----------------------------------------------------------------

class SiteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    allowed_origins: str = ""
    widget_config: dict = Field(default_factory=dict)


class SiteUpdate(BaseModel):
    name: str | None = None
    allowed_origins: str | None = None
    widget_config: dict | None = None
    system_prompt: str | None = None


class SiteOut(BaseModel):
    id: str
    name: str
    allowed_origins: str
    public_key: str
    widget_config: dict
    system_prompt: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Data sources ---------------------------------------------------------

class UrlSourceCreate(BaseModel):
    type: Literal["url"] = "url"
    url: str
    max_pages: int = 200
    max_depth: int = 3
    resync_interval_hours: int = 0  # 0 = disabled, 24 = daily, 168 = weekly


class UploadSourceCreate(BaseModel):
    type: Literal["upload"] = "upload"
    s3_keys: list[str]
    original_names: list[str]


class DataSourceOut(BaseModel):
    id: str
    site_id: str
    type: str
    config: dict
    status: str
    error_message: str | None
    stats: dict
    last_synced_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Widget config (public) -----------------------------------------------

class WidgetConfigOut(BaseModel):
    site_id: str
    name: str
    widget_config: dict
    allowed_origins: list[str]


# --- Upload presigned URL -------------------------------------------------

class PresignRequest(BaseModel):
    filename: str
    content_type: str = "application/octet-stream"


class PresignResponse(BaseModel):
    upload_url: str
    s3_key: str
    expires_in: int


# --- Conversations --------------------------------------------------------

class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    citations: list[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: str
    site_id: str
    visitor_id: str | None
    visitor_identifier: str | None
    created_at: datetime
    messages: list[MessageOut] = []

    class Config:
        from_attributes = True


# --- Analytics ---------------------------------------------------------------

class DailyCount(BaseModel):
    date: str
    count: int


class TopSource(BaseModel):
    source_uri: str
    title: str | None
    citation_count: int


class AnalyticsOut(BaseModel):
    total_conversations: int
    total_messages: int
    conversations_today: int
    conversations_last_7d: int
    daily_conversations: list[DailyCount]
    top_sources: list[TopSource]
    recent_questions: list[str]
