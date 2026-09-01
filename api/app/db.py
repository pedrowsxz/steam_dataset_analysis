"""
api/app/db.py

One shared engine for the process. pool_pre_ping + a modest pool_recycle
exist specifically for Neon's free-tier behavior: compute suspends after
~5 minutes idle, so any connection that's been sitting in the pool across
that gap needs to be detected as dead and transparently replaced rather
than raising on the next request.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings


def _build_engine() -> Engine:
    settings = get_settings()
    url = settings.database_url
    is_local = "localhost" in url or "127.0.0.1" in url
    # Neon requires SSL; local dev/test Postgres doesn't have it configured.
    connect_args = {"sslmode": "require"} if (not is_local and "sslmode=" not in url) else {}
    return create_engine(
        url,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=5,
    )


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()