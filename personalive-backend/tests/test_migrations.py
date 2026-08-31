"""Migration upgrade/downgrade kontrolü.

DİKKAT: bu test gerçek bir şemayı bir kere aşağı (downgrade -1), bir kere
tekrar yukarı (upgrade head) taşıyor — yani DESTRUCTIVE bir işlem. Bu
yüzden asıl geliştirme veritabanı olan DATABASE_URL'i KULLANMAZ, ayrı bir
TEST_DATABASE_URL gerektirir (bkz. DATABASE.md, "Migration testi için
ayrı veritabanı"). TEST_DATABASE_URL tanımlı değilse bu test SKIP edilir.

Güvenlik: hedef veritabanının adında açıkça "test" segmenti yoksa
(örn. yanlışlıkla DATABASE_URL ile aynı veritabanı verilmişse) test
çalışmayı reddeder (FAIL, SKIP değil) — böylece yanlışlıkla gerçek/
geliştirme veritabanı silinip yeniden oluşturulamaz.

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


@requires_test_db
def test_downgrade_then_upgrade_head_succeeds() -> None:
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
