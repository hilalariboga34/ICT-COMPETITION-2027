"""Veritabanı testleri için ortak fixture'lar.

Bu testler GERÇEK bir local PostgreSQL bağlantısı ister (DATABASE_URL,
.env üzerinden) ve şemanın önceden `alembic upgrade head` ile
oluşturulmuş olmasını bekler. DATABASE_URL yoksa ya da veritabanına
ulaşılamıyorsa bu testler otomatik SKIP edilir — böylece veritabanı
kurulmamış bir ortamda (örn. mevcut CI) diğer testler bozulmaz.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session

from app.core.config import get_settings

_DATABASE_URL = get_settings().database_url


def _db_available() -> bool:
    if not _DATABASE_URL:
        return False
    try:
        engine = create_engine(_DATABASE_URL)
        with engine.connect():
            pass
        engine.dispose()
        return True
    except Exception:
        return False


requires_db = pytest.mark.skipif(
    not _db_available(),
    reason=(
        "DATABASE_URL ayarlı değil ya da local PostgreSQL'e ulaşılamıyor. "
        "Bu testler için: .env dosyasında DATABASE_URL tanımlı olmalı ve "
        "hedef veritabanında 'alembic upgrade head' çalıştırılmış olmalı."
    ),
)


@pytest.fixture(scope="session")
def db_engine() -> Iterator[Engine]:
    engine = create_engine(_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_connection(db_engine: Engine) -> Iterator[Connection]:
    connection = db_engine.connect()
    yield connection
    connection.close()


@pytest.fixture()
def db_session(db_connection: Connection) -> Iterator[Session]:
    """Her test kendi transaction'ında çalışır; test bitince tüm
    değişiklikler ROLLBACK edilir. Testler birbirini kirletmez ve
    veritabanına kalıcı veri yazmaz."""
    trans = db_connection.begin()
    session = Session(bind=db_connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
