"""Startup configuration guard rules (config.Settings.validate)."""

import pytest
from student_management.config import (
    DEFAULT_DATABASE_URL,
    DEV_SECRET_KEY,
    POSTGRES_RE,
    Settings,
)

PROD_DATABASE_URL = "postgresql://user@localhost:5432/db"
PROD_SECRET_KEY = "a-very-long-production-secret-key-that-is-32-plus-chars"


def _valid_prod(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", PROD_DATABASE_URL)
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("ALLOWED_HOSTS", "schoolsystem.com")
    monkeypatch.setenv("SECRET_KEY", PROD_SECRET_KEY)


def test_dev_defaults_pass(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("ALLOWED_HOSTS", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    s = Settings()
    assert s.allowed_hosts == ["localhost", "127.0.0.1"]
    assert s.access_token_expire_minutes == 480
    assert s.app_env == "dev"  # dev stays dev, never production

    s.validate()  # no error for the default dev configuration


def test_prod_requires_postgres_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./student_management.db")
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("ALLOWED_HOSTS", "schoolsystem.com")
    monkeypatch.setenv("SECRET_KEY", PROD_SECRET_KEY)

    with pytest.raises(RuntimeError, match="postgresql"):
        Settings().validate()


def test_prod_requires_explicit_allowed_hosts(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", PROD_DATABASE_URL)
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.delenv("ALLOWED_HOSTS", raising=False)
    monkeypatch.setenv("SECRET_KEY", PROD_SECRET_KEY)

    with pytest.raises(RuntimeError, match="ALLOWED_HOSTS"):
        Settings().validate()


def test_prod_requires_explicit_secret_key(monkeypatch):
    _valid_prod(monkeypatch)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        Settings().validate()


def test_prod_rejects_dev_fallback_secret_key(monkeypatch):
    _valid_prod(monkeypatch)
    monkeypatch.setenv("SECRET_KEY", DEV_SECRET_KEY)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        Settings().validate()


def test_prod_rejects_short_secret_key(monkeypatch):
    _valid_prod(monkeypatch)
    monkeypatch.setenv("SECRET_KEY", "too-short")

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        Settings().validate()


def test_prod_accepts_valid_configuration(monkeypatch):
    _valid_prod(monkeypatch)

    s = Settings()
    assert s.app_env == "prod"
    s.validate()  # fully valid production configuration passes


def test_production_alias_normalizes_to_prod(monkeypatch):
    _valid_prod(monkeypatch)
    monkeypatch.setenv("APP_ENV", "production")

    s = Settings()
    assert s.app_env == "prod"
    s.validate()


def test_prod_accepts_postgres_driver_suffix(monkeypatch):
    _valid_prod(monkeypatch)
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user@localhost:5432/db")

    assert POSTGRES_RE is not None
    s = Settings()
    s.validate()


def test_unknown_environment_is_rejected(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    monkeypatch.setenv("APP_ENV", "staging")

    with pytest.raises(RuntimeError, match="APP_ENV"):
        Settings().validate()


def test_non_default_db_without_app_env_is_error(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./custom.db")
    monkeypatch.delenv("APP_ENV", raising=False)

    with pytest.raises(RuntimeError, match="APP_ENV"):
        Settings().validate()


def test_non_default_db_with_app_env_dev_passes(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user@localhost:5432/db")
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("ALLOWED_HOSTS", "localhost")

    s = Settings()
    assert s.app_env == "dev"
    assert s.database_url.startswith("postgresql+psycopg://")
    s.validate()


def test_prod_rejects_wildcard_anywhere_in_allowed_hosts(monkeypatch):
    _valid_prod(monkeypatch)
    monkeypatch.setenv("ALLOWED_HOSTS", "schoolsystem.com,*")

    with pytest.raises(RuntimeError, match="ALLOWED_HOSTS"):
        Settings().validate()


def test_prod_rejects_allowed_hosts_as_bare_wildcard(monkeypatch):
    _valid_prod(monkeypatch)
    monkeypatch.setenv("ALLOWED_HOSTS", "*")

    with pytest.raises(RuntimeError, match="ALLOWED_HOSTS"):
        Settings().validate()


def test_default_db_ignores_app_env_requirement(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    monkeypatch.delenv("APP_ENV", raising=False)

    Settings().validate()  # default URL is allowed without APP_ENV


def test_bare_postgres_url_normalizes_to_psycopg3(monkeypatch):
    _valid_prod(monkeypatch)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user@localhost:5432/db")

    s = Settings()
    assert s.database_url == "postgresql+psycopg://user@localhost:5432/db"
    s.validate()


def test_driver_suffixed_url_is_left_alone(monkeypatch):
    _valid_prod(monkeypatch)
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user@localhost:5432/db")

    s = Settings()
    assert s.database_url == "postgresql+psycopg://user@localhost:5432/db"
    s.validate()


def test_sqlite_url_is_left_alone(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    monkeypatch.delenv("APP_ENV", raising=False)

    s = Settings()
    assert s.database_url == DEFAULT_DATABASE_URL