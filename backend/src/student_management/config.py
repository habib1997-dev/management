"""Application configuration.

Values come from environment variables with sensible development defaults.
For production, set these in the environment or a `.env` file.

Environment meanings (enforced in :meth:`Settings.validate`):
- ``APP_ENV=dev``            Development. Lenient (auto-create tables, relaxed
  guards). The fallback values (SQLite, `localhost` hosts, dev SECRET_KEY) are
  allowed.
- ``APP_ENV=prod``            Production. Strict. Requires ``DATABASE_URL`` to
  start with ``postgresql://`` (a bare ``postgresql://`` is automatically
  mapped onto the psycopg3 driver as ``postgresql+psycopg://``),
  ``ALLOWED_HOSTS`` set explicitly, and an explicit non-default ``SECRET_KEY``
  of at least 32 characters.
- ``APP_ENV=production``      Alias for ``prod`` (normalized at load time).

Anything else (e.g. ``staging``) is a startup error.

A non-default ``DATABASE_URL`` with ``APP_ENV`` unset is also a startup error:
the environment must be confirmed explicitly (``APP_ENV=dev`` or ``=prod``).
"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BACKEND_DIR / ".env")

DEFAULT_DATABASE_URL = "sqlite:///./student_management.db"
DEV_SECRET_KEY = "dev-secret-key-change-me-32bytes-minimum"
VALID_ENVIRONMENTS = ("dev", "prod")
APP_ENV_ALIASES = {"production": "prod"}
POSTGRES_RE = r"^postgresql(?:[+][\w-]+)?://"


def _normalize_database_url(url: str) -> str:
    """Rewrite a bare ``postgresql://`` URL onto the psycopg3 driver.

    Neon (and other hosts) hand out connection strings that start with plain
    ``postgresql://``.  Without a ``+driver`` suffix SQLAlchemy would silently
    pick the psycopg2 dialect, which is NOT installed — the first database
    query would crash with ``ModuleNotFoundError: psycopg2``.  This helper
    maps the bare form to ``postgresql+psycopg://`` so paste-in-string deploy
    "just works".  Non-PostgreSQL URLs (SQLite etc.) and URLs that already
    carry a driver suffix are untouched.
    """
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


class Settings:
    """Runtime settings loaded from the environment."""

    def __init__(self) -> None:
        self.database_url: str = _normalize_database_url(
            os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
        )
        self._database_url_explicit: bool = os.getenv("DATABASE_URL") is not None

        self._app_env_explicit: bool = os.getenv("APP_ENV") is not None
        raw_app_env = os.getenv("APP_ENV", "dev").strip().lower()
        self.app_env: str = APP_ENV_ALIASES.get(raw_app_env, raw_app_env)

        self._secret_key_explicit: bool = os.getenv("SECRET_KEY") is not None
        self.secret_key: str = os.getenv("SECRET_KEY", DEV_SECRET_KEY)
        self.algorithm: str = os.getenv("ALGORITHM", "HS256")
        self.access_token_expire_minutes: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480")
        )

        self._allowed_hosts_explicit: bool = os.getenv("ALLOWED_HOSTS") is not None
        self.allowed_hosts: list[str] = [
            h.strip()
            for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
            if h.strip()
        ]

        self.school_name: str = os.getenv("SCHOOL_NAME", "Usman Public School")
        self.school_tagline: str = os.getenv(
            "SCHOOL_TAGLINE", "Knowledge, Character, Excellence"
        )
        self.brand_primary: str = os.getenv("BRAND_PRIMARY_COLOR", "#0B6B4F")
        self.brand_secondary: str = os.getenv("BRAND_SECONDARY_COLOR", "#D9A441")
        self.brand_demo: bool = os.getenv("BRAND_DEMO", "true").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        self.school_logo_filename: str = os.getenv("SCHOOL_LOGO", "logo.png").strip()

    def validate(self) -> None:
        """Refuse to start with an unsafe or ambiguous configuration."""
        errors: list[str] = []
        if self.app_env not in VALID_ENVIRONMENTS:
            errors.append(
                f"Unsupported APP_ENV={self.app_env!r}. Supported values are "
                "'dev', 'prod' or 'production'."
            )
        if self.app_env == "prod":
            if not re.match(POSTGRES_RE, self.database_url):
                errors.append(
                    "APP_ENV=prod requires DATABASE_URL to start with "
                    "'postgresql://' (a '+' driver suffix such as "
                    "'postgresql+psycopg://' is accepted); got "
                    f"{self.database_url!r}; refusing to run production "
                    "against a non-PostgreSQL database."
                )
            if not self._allowed_hosts_explicit or not self.allowed_hosts:
                errors.append(
                    "APP_ENV=prod requires ALLOWED_HOSTS to be set explicitly; "
                    "the development fallback 'localhost,127.0.0.1' is not allowed "
                    "in production."
                )
            elif "*" in self.allowed_hosts:
                errors.append(
                    "APP_ENV=prod refuses a '*' wildcard in ALLOWED_HOSTS "
                    "(it matches every host). List each host explicitly."
                )
            if (
                not self._secret_key_explicit
                or self.secret_key == DEV_SECRET_KEY
                or len(self.secret_key) < 32
            ):
                errors.append(
                    "APP_ENV=prod requires SECRET_KEY to be set explicitly with "
                    "a value different from the development default and at "
                    "least 32 characters long."
                )
        if (
            self._database_url_explicit
            and self.database_url != DEFAULT_DATABASE_URL
            and not self._app_env_explicit
        ):
            errors.append(
                "A non-default DATABASE_URL is set but APP_ENV is not. "
                "Set APP_ENV=dev, APP_ENV=prod or APP_ENV=production in the "
                "environment to confirm the intended environment."
            )
        if errors:
            raise RuntimeError(
                "Invalid configuration:\n" + "\n".join(f"- {e}" for e in errors)
            )


settings = Settings()
settings.validate()