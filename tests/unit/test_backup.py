"""Unit tests for the online backup/restore helpers (SQLite branch)."""

import importlib.util
import os
import sqlite3
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
SPEC = importlib.util.spec_from_file_location("backup_script", REPO / "backend" / "scripts" / "backup.py")
backup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(backup)


def _make_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("INSERT INTO items (name) VALUES ('alpha'), ('beta')")
    conn.commit()
    conn.close()


def test_sqlite_backup_round_trip_restores_data(tmp_path):
    db = tmp_path / "data.db"
    _make_db(db)

    backup_file = tmp_path / "backup.db"
    backup.backup_to_file(f"sqlite:///{db}", backup_file)
    assert backup_file.is_file() and backup_file.stat().st_size > 0

    conn = sqlite3.connect(db)
    conn.execute("DROP TABLE items")
    conn.commit()
    conn.close()

    backup.restore_from_file(f"sqlite:///{db}", backup_file)

    conn = sqlite3.connect(db)
    rows = conn.execute("SELECT name FROM items ORDER BY id").fetchall()
    conn.close()
    assert rows == [("alpha",), ("beta",)]


def test_backup_suffix_by_database_type():
    assert backup.backup_suffix("sqlite:///./student_management.db") == ".db"
    assert backup.backup_suffix("postgresql://user@host/db") == ".dump"
    assert backup.backup_suffix("postgresql+psycopg://user@host/db") == ".dump"


def test_is_postgres_matches_plain_and_driver_urls():
    assert backup.is_postgres("postgresql://user@host/db") is True
    assert backup.is_postgres("postgresql+psycopg://user@host/db") is True
    assert backup.is_postgres("sqlite:///./student_management.db") is False


def test_sqlite_db_path_resolves_relative_to_backend(tmp_path):
    # absolute paths are used verbatim
    assert backup.sqlite_db_path(f"sqlite:///{tmp_path}/x.db") == (tmp_path / "x.db").resolve()


def test_postgres_env_sets_credentials_and_ssl_from_url():
    env = backup.postgres_env(
        "postgresql+psycopg://alice:s3cret@db.example.com:5544/myschool?sslmode=require"
    )
    assert env["PGHOST"] == "db.example.com"
    assert env["PGPORT"] == "5544"
    assert env["PGUSER"] == "alice"
    assert env["PGPASSWORD"] == "s3cret"
    assert env["PGDATABASE"] == "myschool"
    assert env["PGSSLMODE"] == "require"


def test_postgres_env_omits_password_and_ssl_when_absent():
    env = backup.postgres_env("postgresql://alice@db.example.com/myschool")
    assert "PGPASSWORD" not in env
    assert "PGSSLMODE" not in env
    assert env["PGUSER"] == "alice"
    assert env["PGDATABASE"] == "myschool"


def test_postgres_env_merges_with_existing_environment():
    env = backup.postgres_env("postgresql://alice@db.example.com/myschool")
    assert env["PATH"] == os.environ["PATH"]
    assert env["PGUSER"] == "alice"


def test_postgres_restore_requires_maintenance(monkeypatch):
    monkeypatch.setattr(backup.settings, "database_url", "postgresql://user@host/db")
    with pytest.raises(SystemExit):
        backup.main(["--restore", "--file", "unused.dump", "--confirm"])


def test_sqlite_restore_does_not_require_maintenance(monkeypatch):
    monkeypatch.setattr(
        backup.settings, "database_url", "sqlite:///./student_management.db"
    )
    with pytest.raises(SystemExit):
        backup.main(["--restore", "--file", "missing.db", "--confirm"])