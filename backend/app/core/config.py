"""Centralised typed settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    env: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me"
    service_name: str = "api"

    # Database
    database_url: str = "postgresql+psycopg://rag:rag@postgres:5432/rag"

    # Redis / Celery
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    # Object store (MinIO / S3)
    s3_endpoint_url: str = "http://minio:9000"
    # Browser-reachable endpoint for presigned upload URLs (defaults to s3_endpoint_url).
    s3_public_endpoint_url: str = ""
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "rag-uploads"
    s3_region: str = "us-east-1"

    # LLM provider
    llm_provider: Literal["openai", "ollama", "gemini", "minimax"] = "openai"
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    openai_embed_model: str = "text-embedding-3-small"
    ollama_base_url: str = "http://ollama:11434"
    ollama_chat_model: str = "llama3.1:8b-instruct"
    gemini_api_key: str = ""
    gemini_chat_model: str = "gemini-2.0-flash"
    minimax_api_key: str = ""
    minimax_chat_model: str = "MiniMax-Text-01"
    minimax_base_url: str = "https://api.minimaxi.chat/v1"

    # Embeddings
    embed_provider: Literal["local", "openai"] = "local"
    embed_model_local: str = "BAAI/bge-small-en-v1.5"
    embed_dim: int = 384

    # CORS
    api_cors_origins: str = "http://portal.localhost,http://localhost:5173"

    # Auth / cookies
    session_cookie_name: str = "rag_session"
    session_cookie_domain: str = ""
    session_cookie_secure: bool = False
    session_ttl_seconds: int = 30 * 24 * 3600

    # Crawler
    crawl_max_pages: int = 200
    crawl_max_depth: int = 3
    crawl_user_agent: str = "RAGSiteAssistantBot/1.0"
    crawl_timeout_seconds: int = 20

    # Chat
    chat_max_context_chunks: int = 6
    chat_history_turns: int = 6
    chat_rate_limit_per_min: int = 30
    # Cosine distance threshold (0=identical, 1=orthogonal, 2=opposite).
    # Chunks above this are discarded; if none pass, the canned fallback is returned.
    chat_context_distance_threshold: float = 0.5

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]

    @property
    def s3_presign_endpoint_url(self) -> str:
        return self.s3_public_endpoint_url or self.s3_endpoint_url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
