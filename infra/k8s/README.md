# Production deployment (k3s)

Minimal cluster layout (single-node k3s is fine to start, but recommend 3
nodes for production HA).

## Pods

- `postgres`     — postgres 16 with pgvector. Persistent volume for `/var/lib/postgresql/data`.
- `redis`        — single replica, AOF on a small PV.
- `minio`        — single tenant, PV for `/data`. Run an init Job to create the bucket.
- `api`          — `rag-backend:dev` with `CMD ["api"]`. Replicas: 2. Liveness: `GET /health`.
- `chat-server`  — `rag-backend:dev` with `CMD ["chat"]`. HPA on connection count or CPU. Replicas: 2–10.
- `worker`       — `rag-backend:dev` with `CMD ["worker"]`. Replicas: 1–3. May want a node selector for GPU if you swap to Ollama.
- `portal`       — `rag-portal:dev` (nginx serving static). Replicas: 2.
- `widget`       — `rag-widget:dev` (nginx serving `/chat.js`). Replicas: 2 + edge cache.
- `traefik`      — comes with k3s. Configure IngressRoutes for `api.`, `chat.`, `portal.`, `cdn.<domain>`.

## TLS

Traefik + cert-manager + Let's Encrypt. One `Certificate` per public hostname,
or use a wildcard via DNS-01.

## Secrets

Use `kubectl create secret generic rag-env --from-env-file=.env`. Mount it as
`envFrom` on api / chat-server / worker.

## Migrations

Run `alembic upgrade head` as an init container on the `api` Deployment, or as
a dedicated one-shot `Job` per release.

## Backups

- Postgres: `pg_dump` to S3 nightly via a CronJob.
- MinIO: replicate to a remote S3 endpoint (`mc mirror`).

## Scaling notes

- `chat-server` is the hot path: long-lived SSE connections, blocks on LLM I/O.
  Use an HPA on `nginx_ingress_active_connections` or per-pod CPU.
- `worker` is bursty (ingest jobs). Use a Celery autoscaler or KEDA with the
  Redis broker queue depth as the metric.
- `pgvector` ivfflat scales to tens of millions of vectors on one node. Switch
  to HNSW (newer index type) or Qdrant only when you actually hit the wall.
