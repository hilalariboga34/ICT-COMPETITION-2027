"""Migration upgrade/downgrade kontrolü.

DİKKAT: bu test gerçek bir şemayı bir kere aşağı (downgrade -1), bir kere
tekrar yukarı (upgrade head) taşıyor — yani DESTRUCTIVE bir işlem. Bu
yüzden asıl geliştirme veritabanı olan DATABASE_URL'i KULLANMAZ, ayrı bir
TEST_DATABASE_URL gerektirir (bkz. DATABASE.md, "Migration testi için
ayrı veritabanı"). TEST_DATABASE_URL tanımlı değilse bu test SKIP edilir.

Güvenlik: iki ayrı kontrol var, ikisi de FAIL verir (SKIP değil):
1) TEST_DATABASE_URL, DATABASE_URL ile AYNI veritabanını gösteriyorsa
   (host + port + veritabanı adı aynıysa) — kullanıcı adı/şifre farklı
   yazılmış olsa bile yakalanır.
2) Veritabanı adında açıkça "test" segmenti yoksa (örn. yanlışlıkla
   başka bir gerçek veritabanı verilmişse).
Böylece yanlışlıkla gerçek/geliştirme veritabanı silinip yeniden
oluşturulamaz.

Diğer DB testleriyle karışık sırada DEĞİL, tek başına çalıştırılması
önerilir:

    pytest tests/test_migrations.py -v
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from app.core.config import get_settings

_TEST_DATABASE_URL = get_settings().test_database_url
_DATABASE_URL = get_settings().database_url

requires_test_db = pytest.mark.skipif(
    not _TEST_DATABASE_URL,
    reason=(
        "TEST_DATABASE_URL tanımlı değil. Migration testi kendi ayrı "
        "veritabanını gerektirir (bkz. DATABASE.md, 'Migration testi için "
        "ayrı veritabanı') — asıl DATABASE_URL'i KULLANMAZ."
    ),
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _database_name(url: str) -> str:
    # SQLAlchemy URL'sinde path kısmı "/veritabani_adi" şeklinde gelir.
    return urlsplit(url).path.lstrip("/")


def _database_identity(url: str) -> tuple[str | None, int | None, str]:
    # Kullanıcı adı/şifre farklı yazılmış olsa bile "aynı veritabanı mı"
    # sorusunun cevabı host + port + veritabanı adı üçlüsüdür.
    parts = urlsplit(url)
    return (parts.hostname, parts.port, parts.path.lstrip("/"))


def _ensure_not_same_as_database_url(test_url: str, database_url: str | None) -> None:
    """Hilal'in bulduğu nokta: TEST_DATABASE_URL, asıl DATABASE_URL ile
    AYNI veritabanını gösteriyorsa bu test kesinlikle FAIL vermeli —
    yoksa downgrade/upgrade döngüsü doğrudan geliştirme verisini bozar.
    "test" isim kontrolünden AYRI ve ondan ÖNCE çalışır: isimde "test"
    geçse bile, iki adres aynı veritabanını gösteriyorsa yine reddedilir.
    """
    if database_url is None:
        return
    if _database_identity(test_url) == _database_identity(database_url):
        pytest.fail(
            "TEST_DATABASE_URL, DATABASE_URL ile AYNI veritabanını "
            "gösteriyor. Migration testi downgrade/upgrade yaptığı için "
            "bu durumda asıl geliştirme veritabanını bozar — bu yüzden "
            "reddedildi. TEST_DATABASE_URL'i ayrı, sadece bu test için "
            "var olan bir veritabanına (örn. personalive_backend_test_db) "
            "yönlendir."
        )


def _ensure_looks_like_test_database(url: str) -> None:
    """TEST_DATABASE_URL yanlışlıkla gerçek/geliştirme veritabanını mı
    gösteriyor diye son bir güvenlik kontrolü. Veritabanı adında ayrı bir
    "test" segmenti (örn. personalive_backend_test_db) olmalı."""
    name = _database_name(url)
    segments = name.split("_")
    if "test" not in segments:
        pytest.fail(
            f"TEST_DATABASE_URL güvenli görünmüyor: veritabanı adı "
            f"'{name}' içinde ayrı bir 'test' segmenti yok. Yanlışlıkla "
            "gerçek/geliştirme veritabanını downgrade/upgrade ile "
            "bozmamak için bu test reddedildi — TEST_DATABASE_URL'i "
            "adında açıkça 'test' geçen (örn. personalive_backend_test_db) "
            "ayrı bir veritabanına yönlendir."
        )


def _run_alembic(*args: str) -> None:
    # DATABASE_URL'i SADECE bu subprocess için TEST_DATABASE_URL'e
    # çeviriyoruz — asıl process'in ortam değişkenine dokunmuyoruz.
    env = {**os.environ, "DATABASE_URL": _TEST_DATABASE_URL or ""}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr


def _current_head() -> str:
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    head = script.get_current_head()
    assert head is not None
    return head


def test_ensure_not_same_as_database_url_rejects_identical_database() -> None:
    """Hilal'in bulduğu nokta: TEST_DATABASE_URL, DATABASE_URL ile aynı
    veritabanını gösteriyorsa (host+port+ad aynıysa) reddedilmeli —
    kullanıcı adı/şifre farklı yazılmış olsa bile. Gerçek DB bağlantısı
    gerektirmez, saf bir birim testidir."""
    database_url = "postgresql+psycopg://app:secret@localhost:5432/personalive_backend_test_db"
    test_url_same_db_different_creds = (
        "postgresql+psycopg://baska_kullanici:baska_sifre@localhost:5432/"
        "personalive_backend_test_db"
    )
    with pytest.raises(pytest.fail.Exception):
        _ensure_not_same_as_database_url(test_url_same_db_different_creds, database_url)


def test_ensure_not_same_as_database_url_allows_genuinely_different_database() -> None:
    database_url = "postgresql+psycopg://app:secret@localhost:5432/personalive_backend_db"
    test_url = "postgresql+psycopg://app:secret@localhost:5432/personalive_backend_test_db"
    _ensure_not_same_as_database_url(test_url, database_url)  # exception atmamalı


def test_ensure_not_same_as_database_url_allows_when_database_url_unset() -> None:
    test_url = "postgresql+psycopg://app:secret@localhost:5432/personalive_backend_test_db"
    _ensure_not_same_as_database_url(test_url, None)  # exception atmamalı


@requires_test_db
def test_downgrade_then_upgrade_head_succeeds() -> None:
    _ensure_not_same_as_database_url(_TEST_DATABASE_URL, _DATABASE_URL)
    _ensure_looks_like_test_database(_TEST_DATABASE_URL)

    head = _current_head()
    engine = create_engine(_TEST_DATABASE_URL)
    try:
        with engine.connect() as conn:
            before = conn.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar()
        assert before == head, (
            "Teste başlamadan önce test veritabanı 'head' revizyonunda "
            "olmalı (önce TEST_DATABASE_URL üzerinde 'alembic upgrade "
            "head' çalıştır)."
        )

        _run_alembic("downgrade", "-1")
        with engine.connect() as conn:
            tables = (
                conn.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'public'"
                    )
                )
                .scalars()
                .all()
            )
        assert "sessions" not in tables
        assert "manipulation_methods" not in tables

        _run_alembic("upgrade", "head")
        with engine.connect() as conn:
            after = conn.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar()
        assert after == head
    except Exception:
        # Test yarıda kaldıysa (assertion ya da alembic hatası), test
        # veritabanını tekrar 'head'e yükseltmeyi dene ki bozuk/eksik
        # şema halinde kalmasın.
        _run_alembic("upgrade", "head")
        raise
    finally:
        engine.dispose()
