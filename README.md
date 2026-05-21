# RAG Site Assistant

Self-hosted multi-tenant RAG platform. Site owners embed a `<script>` tag on
their site, configure a knowledge source (URL crawl or document upload) in the
portal, and visitors get an AI assistant grounded in that data.

## Architecture

- **Python services (all AI / data plane)**
  - `api` — FastAPI REST API (auth, sites, sources, widget config)
  - `chat-server` — FastAPI SSE server for visitor chat (RAG query path)
  - `worker` — Celery worker for ingestion (crawl, parse, chunk, embed)
- **TypeScript surfaces (UI only)**
  - `portal/` — React + Vite SPA owner dashboard
  - `widget/` — Embeddable browser widget (single `chat.js`)
- **Data**
  - PostgreSQL 16 + `pgvector` (single source of truth + vector store)
  - Redis (Celery broker + rate limits + cache)
  - MinIO (S3-compatible object store for uploads)
- **Edge**: Traefik with TLS via Let's Encrypt (prod) / self-signed (dev)

## Quick start (local dev)

Prereqs: Docker + Docker Compose.

```bash
cp .env.example .env
# fill in OPENAI_API_KEY (default), GEMINI_API_KEY, or set LLM_PROVIDER=ollama

docker compose up -d postgres redis minio
docker compose up --build api chat-server worker static-web traefik
```

Then open:

- Portal: <http://portal.localhost>
- API:    <http://api.localhost/docs>
- Chat:   <http://chat.localhost/docs>
- MinIO:  <http://localhost:9001> (minioadmin / minioadmin)

## Repo layout

```
backend/        Python — all data-plane services share one package
  app/api/        REST API entrypoint
  app/chat_server/  Chat / SSE entrypoint
  app/workers/    Celery worker entrypoint
  app/rag/        Shared retrieval / embedding / LLM client
  app/models/     SQLAlchemy models
  app/core/       Config, security, DB session, deps
  alembic/        DB migrations
portal/         React + Vite SPA (TypeScript)
widget/         Embeddable widget (TypeScript, Vite single-file build)
infra/          docker-compose, k8s manifests, Traefik config
```

## Tenant isolation

Every query against `chunks` MUST filter by `site_id`. Retrieval is encapsulated
in `app.rag.retriever.SiteScopedRetriever` so no caller can forget. Widget
endpoints additionally check the request `Origin` against the site's domain
allowlist.

## LLM provider

Set `LLM_PROVIDER=openai` (default), `LLM_PROVIDER=ollama`, or `LLM_PROVIDER=gemini`.
Same interface, no code changes — see `app/rag/llm_client.py`.
