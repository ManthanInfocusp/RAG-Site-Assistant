"""Tiny ops CLI: smoke-test ingestion and retrieval without the HTTP layer.

Usage examples (run inside the backend container):

    python -m app.cli embed-and-search "<site_id>" "<query>"
    python -m app.cli ingest-source "<source_id>"
"""

from __future__ import annotations

import argparse
import sys

from app.core.db import SessionLocal
from app.rag.embedder import get_embedder
from app.rag.retriever import SiteScopedRetriever


def cmd_embed_and_search(args: argparse.Namespace) -> int:
    db = SessionLocal()
    try:
        [vec] = get_embedder().embed([args.query])
        results = SiteScopedRetriever(db, args.site_id).search(vec, k=args.k)
        for r in results:
            print(f"[d={r.distance:.4f}] {r.title or r.source_uri}")
            print((r.content[:300] + "...") if len(r.content) > 300 else r.content)
            print("-" * 80)
    finally:
        db.close()
    return 0


def cmd_ingest_source(args: argparse.Namespace) -> int:
    from app.workers.tasks.ingest import ingest_data_source

    # Run synchronously instead of via Celery.
    result = ingest_data_source.run(args.source_id)
    print(result)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rag-cli")
    sub = parser.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("embed-and-search")
    s1.add_argument("site_id")
    s1.add_argument("query")
    s1.add_argument("-k", type=int, default=6)
    s1.set_defaults(func=cmd_embed_and_search)

    s2 = sub.add_parser("ingest-source")
    s2.add_argument("source_id")
    s2.set_defaults(func=cmd_ingest_source)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
