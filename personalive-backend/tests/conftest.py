"""Veritabanı testleri için ortak fixture'lar.

Bu testler GERÇEK bir local PostgreSQL bağlantısı ister (DATABASE_URL,
.env üzerinden) ve şemanın önceden `alembic upgrade head` ile
oluşturulmuş olmasını bekler. DATABASE_URL hiç tanımlı değilse bu testler
otomatik SKIP edilir — böylece veritabanı kurulmamış bir ortamda (örn.
DATABASE_URL'siz local çalıştırma) diğer testler bozulmaz.

ÖNEMLİ (Hilal'in bulduğu nokta): DATABASE_URL TANIMLIYKEN bağlantı
kurulamıyorsa bu artık SKIP değil, FAIL olarak görünür — yani CI'da
DATABASE_URL set edilmiş ama Postgres servisi ayağa kalkmamışsa (ya da
yanlış yapılandırılmışsa) testler yeşile boyanıp yanıltmaz, gerçekten
kırmızı görünür. Bu yüzden aşağıda "bağlantı kurulabiliyor mu" diye ayrı
bir kontrol YOK — sadece "DATABASE_URL var mı" diye bakıyoruz; bağlantı
denemesi fixture'ların içinde (db_connection) doğal olarak yapılıyor ve
başarısız olursa test hatası olarak patlıyor.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session

from app.core.config import get_settings

_DATABASE_URL = get_settings().database_url

requires_db = pytest.mark.skipif(
    not _DATABASE_URL,
    reason=(
        "DATABASE_URL tanımlı değil. Bu testler için: .env dosyasında "
        "DATABASE_URL tanımlı olmalı ve hedef veritabanında "
        "'alembic upgrade head' çalıştırılmış olmalı."
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
