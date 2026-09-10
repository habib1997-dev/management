"""Online database backup and restore for the student-management system.

Run from the backend directory:

    python -m scripts.backup                          # take a backup
    python -m scripts.backup --list                    # show existing backups
    python -m scripts.backup --restore --file X --confirm --maintenance

Safety guarantees:
- SQLite is backed up with its built-in *online* backup API (a raw copy of a
  live database file can corrupt data; this never copies a file).
- PostgreSQL uses ``pg_dump``/``pg_restore``. Connection settings are read from
  the ``DATABASE_URL`` (host/port/user/password/database plus query-string
  options such as ``sslmode=require``, required by Neon) and passed to the tools
  as ``PG*`` environment variables - credentials never appear on a command
  line and SSL settings are preserved.
- Restore is refused without ``--confirm`` and, for PostgreSQL, without
  ``--maintenance`` (an acknowledgement that the live web service has been
  stopped first - see below). Restore ALWAYS snapshots the current data first
  (a timestamped ``pre_restore_*`` file), so nothing is ever overwritten
  casually.

Restoring while the web app is still running can clobber data mid-flight or
lose writes. On PostgreSQL you MUST stop the web service before restoring;
``--maintenance`` is your acknowledgement that you have done so - it is a
safety confirmation, not a mechanism that protects a running service.

Backups go to ``backend/backups/``. That folder is in ``.gitignore`` and must
never be committed. For a real deployment, keep the backups encrypted and on
separate storage outside the web server's public files and document-library
location.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from student_management.config import settings

BACKENDS_DIR = Path(__file__).resolve().parent.parent
BACKUPS_DIR = BACKENDS_DIR / "backups"

SQLITE_PREFIX = "sqlite:///"
POSTGRES_PREFIX = "postgresql"

# Query-string options in the DB URL that map onto libpq/PG* environment
# variables. `sslmode=require` (Neon) is the critical one.
_PG_QUERY_TO_ENV = {
    "sslmode": "PGSSLMODE",
    "sslcert": "PGSSLCERT",
    "sslkey": "PGSSLKEY",
    "sslrootcert": "PGSSLROOTCERT",
    "sslcrl": "PGSSLCRL",
    "application_name": "PGAPPNAME",
    "connect_timeout": "PGCONNECT_TIMEOUT",
}


def is_sqlite(db_url: str) -> bool:
    return db_url.startswith(SQLITE_PREFIX)


def is_postgres(db_url: str) -> bool:
    return db_url.startswith(POSTGRES_PREFIX)


def sqlite_db_path(db_url: str) -> Path:
    raw = db_url[len(SQLITE_PREFIX) :]
    path = Path(raw)
    if not path.is_absolute():
        path = (BACKENDS_DIR / path).resolve()
    return path


def backup_suffix(db_url: str) -> str:
    return ".db" if is_sqlite(db_url) else ".dump"


def postgres_env(db_url: str) -> dict[str, str]:
    """Build the environment for ``pg_dump``/``pg_restore`` from a DB URL.

    Returns a copy of the current process environment augmented with the
    ``PG*`` connection variables parsed from ``db_url`` (``postgresql://`` or
    ``postgresql+psycopg://``). The password, if any, is passed through the
    environment so it never shows up in a command line or process listing.
    Query-string options (e.g. ``sslmode=require``) are preserved as their
    corresponding ``PG*`` variables.
    """
    env = os.environ.copy()
    parsed = urlparse(db_url)
    if parsed.username:
        env["PGUSER"] = parsed.username
    if parsed.password is not None:
        env["PGPASSWORD"] = parsed.password
    if parsed.hostname:
        env["PGHOST"] = parsed.hostname
    try:
        port = parsed.port
    except ValueError:
        port = None
    if port is not None:
        env["PGPORT"] = str(port)
    database = parsed.path.lstrip("/")
    if database:
        env["PGDATABASE"] = database
    for key, value in parse_qs(parsed.query).items():
        pg_var = _PG_QUERY_TO_ENV.get(key.lower())
        if pg_var is not None and value:
            env[pg_var] = value[0]
    return env


def _pg_dump(db_url: str, out_path: Path) -> None:
    with out_path.open("wb") as handle:
        subprocess.run(
            ["pg_dump", "--format=custom", "--file=-"],
            check=True,
            stdout=handle,
            env=postgres_env(db_url),
        )


def _pg_restore(db_url: str, backup_file: Path) -> None:
    subprocess.run(
        [
            "pg_restore",
            "--clean",
            "--if-exists",
            "--no-owner",
            str(backup_file),
        ],
        check=True,
        env=postgres_env(db_url),
    )


def backup_to_file(db_url: str, out_path: Path) -> None:
    """Write an online snapshot of the database to ``out_path``."""
    if is_sqlite(db_url):
        source = sqlite3.connect(sqlite_db_path(db_url))
        destination = sqlite3.connect(out_path)
        try:
            with destination:
                source.backup(destination)
        finally:
            destination.close()
            source.close()
    else:
        _pg_dump(db_url, out_path)


def restore_from_file(db_url: str, backup_file: Path) -> None:
    """Restore the database from ``backup_file``.

    Callers MUST take a pre-restore snapshot first (see ``main``).
    """
    if is_sqlite(db_url):
        source = sqlite3.connect(backup_file)
        destination = sqlite3.connect(sqlite_db_path(db_url))
        try:
            with source:
                source.backup(destination)
        finally:
            destination.close()
            source.close()
    else:
        _pg_restore(db_url, backup_file)


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d-%H%M%S")


def list_backups() -> list[Path]:
    if not BACKUPS_DIR.is_dir():
        return []
    return sorted(BACKUPS_DIR.glob("student_management_*"), reverse=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Online database backup/restore. Backups land in backend/backups/ "
            "(git-ignored). Restore requires --confirm and always snapshots the "
            "current data first. On PostgreSQL, restore also requires "
            "--maintenance: stop the live web service before restoring; "
            "--maintenance is your acknowledgement that you have done so."
        )
    )
    parser.add_argument("--restore", action="store_true", help="restore from a backup file")
    parser.add_argument("--file", type=Path, help="backup file to restore from")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="acknowledge that the restore will replace the current data",
    )
    parser.add_argument(
        "--maintenance",
        action="store_true",
        help="(PostgreSQL) acknowledge that the live web service is stopped",
    )
    parser.add_argument("--list", action="store_true", help="list existing backups")
    args = parser.parse_args(argv)

    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    db_url = settings.database_url
    suffix = backup_suffix(db_url)

    if args.list:
        found = list_backups()
        if not found:
            print("No backups found in backups/.")
            return 0
        for item in found:
            print(item.name)
        return 0

    if args.restore:
        if args.file is None or not args.confirm:
            parser.error("--restore requires both --file <path> and --confirm.")
        if is_postgres(db_url) and not args.maintenance:
            parser.error(
                "--restore on PostgreSQL requires --maintenance. Stop the live web "
                "service first (the app must not be running while the database is "
                "restored), then pass --maintenance to acknowledge that you have."
            )
        if not args.file.is_file():
            parser.error(f"Backup file not found: {args.file}")
        pre = BACKUPS_DIR / f"pre_restore_{_timestamp()}{suffix}"
        print("Creating a pre-restore snapshot of the CURRENT data ...")
        backup_to_file(db_url, pre)
        print(f"  -> {pre.name}")
        print(f"Restoring from {args.file} ...")
        restore_from_file(db_url, args.file)
        print("Restore complete.")
        return 0

    out = BACKUPS_DIR / f"student_management_{_timestamp()}{suffix}"
    try:
        backup_to_file(db_url, out)
    except (sqlite3.Error, subprocess.CalledProcessError) as exc:
        out.unlink(missing_ok=True)
        print(f"Backup failed: {exc}", file=sys.stderr)
        return 1
    print(f"Backup written to {out}")

    # Reminder for real deployments, where a local backup is not enough.
    if not is_sqlite(db_url):
        print(
            "Deployment note: store this file encrypted and off-server (e.g. an "
            "object store / vault) - never inside the web server's public files."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())