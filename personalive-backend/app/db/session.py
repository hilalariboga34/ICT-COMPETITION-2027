from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session as SASession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        if not settings.database_url:
            raise RuntimeError(
                "DATABASE_URL ayarlanmamış — .env dosyasında DATABASE_URL tanımlı mı kontrol et."
            )
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
    return _engine


def get_sessionmaker() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(), autoflush=False, autocommit=False
        )
    return _SessionLocal


def get_db_session() -> Iterator[SASession]:
    """FastAPI dependency that provides one SQLAlchemy session per request.

    Transaction boundaries belong to the service using the session. Keeping this
    dependency separate from ``get_session`` also lets API tests replace it with
    the rollback-protected ``db_session`` fixture.
    """
    session_local = get_sessionmaker()
    session = session_local()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def get_session() -> Iterator[SASession]:
    """`with get_session() as session:` şeklinde kullanılır.
    Blok hatasız biterse otomatik commit, hata olursa otomatik rollback yapar."""
    session_local = get_sessionmaker()
    session = session_local()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def test_connection() -> bool:
    """Basit bağlantı testi: SELECT 1 çalıştırır, başarılıysa True döner."""
    with get_session() as session:
        session.execute(text("SELECT 1"))
    return True
