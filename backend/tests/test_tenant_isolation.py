"""Tenant isolation guard-rails.

These are pure unit tests — no DB required. They verify two non-negotiable
invariants of the RAG layer:

1. `SiteScopedRetriever` rejects empty / falsy site_id at construction time.
2. Every SQL statement it emits contains a `chunks.site_id = :param` predicate
   bound to the configured site_id.
"""

from __future__ import annotations

import pytest

from app.rag.retriever import SiteScopedRetriever


class _CapturingSession:
    """Minimal SQLAlchemy session stub that records `execute` statements."""

    def __init__(self) -> None:
        self.statements: list = []

    def execute(self, stmt):
        self.statements.append(stmt)

        class _Result:
            def all(self):
                return []

        return _Result()


def test_retriever_rejects_empty_site_id():
    with pytest.raises(ValueError):
        SiteScopedRetriever(_CapturingSession(), "")  # type: ignore[arg-type]


def test_retriever_query_includes_site_id_filter():
    session = _CapturingSession()
    retriever = SiteScopedRetriever(session, "site-abc")  # type: ignore[arg-type]
    retriever.search([0.0] * 384, k=5)

    assert len(session.statements) == 1
    compiled = str(session.statements[0].compile(compile_kwargs={"literal_binds": True}))
    assert "chunks.site_id" in compiled
    assert "'site-abc'" in compiled
    assert "LIMIT 5" in compiled
