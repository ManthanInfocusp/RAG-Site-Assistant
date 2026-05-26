"""SQLAlchemy engine + session factory.

We use a single sync engine. Embedding / LLM calls happen outside the DB
transaction, so async DB isn't worth the complexity for our use-case.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# pgvector IVFFlat defaults to probes=1, which can return zero rows on small
# indexes (e.g. lists=100 with ~50 chunks). Tune per connection instead.
IVFFLAT_PROBES = 10


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    future=True,
)


@event.listens_for(engine, "connect")
def _set_pgvector_probes(dbapi_connection, _connection_record) -> None:
    with dbapi_connection.cursor() as cursor:
        cursor.execute(f"SET ivfflat.probes = {IVFFLAT_PROBES}")


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
