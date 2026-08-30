"""Migration upgrade/downgrade kontrolü.

DİKKAT: bu test gerçek şemayı bir kere aşağı (downgrade -1), bir kere
tekrar yukarı (upgrade head) taşır. Diğer DB testleriyle karışık sırada
DEĞİL, tek başına çalıştırılması önerilir:

    pytest tests/test_migrations.py -v

Gerçek local PostgreSQL gerektirir (bkz. conftest.requires_db)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from tests.conftest import _DATABASE_URL, requires_db

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _run_alembic(*args: str) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr


def _current_head() -> str:
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    head = script.get_current_head()
    assert head is not None
    return head


@requires_db
def test_downgrade_then_upgrade_head_succeeds() -> None:
    head = _current_head()
    engine = create_engine(_DATABASE_URL)

    with engine.connect() as conn:
        before = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    assert before == head, "Teste başlamadan önce şema 'head' revizyonunda olmalı."

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
        after = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    assert after == head

    engine.dispose()
