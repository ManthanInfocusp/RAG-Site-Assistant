"""Prometheus metrics shared by all Python services.

Each service mounts `/metrics` and `/health`. Counters and histograms are
defined once at module import; FastAPI middleware updates them per request.
"""

from __future__ import annotations

import time

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

from app.core.config import settings

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests by service, method, route, status",
    ["service", "method", "route", "status"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency by service / route",
    ["service", "method", "route"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)
chat_tokens_streamed_total = Counter(
    "chat_tokens_streamed_total",
    "Tokens streamed back to chat clients",
    ["site_id"],
)
ingest_chunks_total = Counter(
    "ingest_chunks_total",
    "Chunks indexed during ingestion",
    ["site_id", "source_type"],
)


def install(app: FastAPI) -> None:
    @app.middleware("http")
    async def _metrics_middleware(request: Request, call_next):
        # Skip the metrics endpoint itself.
        if request.url.path == "/metrics":
            return await call_next(request)
        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed = time.perf_counter() - start
        route = request.scope.get("route")
        route_path = getattr(route, "path", request.url.path)
        http_requests_total.labels(
            service=settings.service_name,
            method=request.method,
            route=route_path,
            status=str(response.status_code),
        ).inc()
        http_request_duration_seconds.labels(
            service=settings.service_name,
            method=request.method,
            route=route_path,
        ).observe(elapsed)
        return response

    @app.get("/metrics")
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
