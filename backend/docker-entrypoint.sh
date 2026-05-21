#!/usr/bin/env bash
set -euo pipefail

cmd="${1:-api}"

case "$cmd" in
  api)
    echo "[entrypoint] starting api on :8000"
    alembic upgrade head
    exec uvicorn app.api.main:app --host 0.0.0.0 --port 8000
    ;;
  chat)
    echo "[entrypoint] starting chat-server on :8001"
    exec uvicorn app.chat_server.main:app --host 0.0.0.0 --port 8001
    ;;
  worker)
    echo "[entrypoint] starting celery worker"
    exec celery -A app.workers.celery_app worker --loglevel=info --concurrency=2
    ;;
  beat)
    echo "[entrypoint] starting celery beat"
    exec celery -A app.workers.celery_app beat --loglevel=info
    ;;
  cli)
    shift
    exec python -m app.cli "$@"
    ;;
  shell)
    exec /bin/bash
    ;;
  *)
    echo "Unknown command: $cmd"
    echo "Usage: $0 {api|chat|worker|beat|cli|shell}"
    exit 1
    ;;
esac
