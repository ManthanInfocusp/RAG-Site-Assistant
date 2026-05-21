"""Celery app + task discovery."""

from __future__ import annotations

from celery import Celery

from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()

celery_app = Celery(
    "rag",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    timezone="UTC",
)

# Discover tasks.
celery_app.autodiscover_tasks(["app.workers.tasks"])

# Import to ensure tasks register even when autodiscover misses (running locally).
from app.workers.tasks import ingest  # noqa: E402,F401
