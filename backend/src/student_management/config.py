"""Application configuration.

Values come from environment variables with sensible development defaults.
For production, set these in the environment or a `.env` file.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BACKEND_DIR / ".env")


class Settings:
    """Runtime settings loaded from the environment."""

    def __init__(self) -> None:
        self.database_url: str = os.getenv(
            "DATABASE_URL", "sqlite:///./student_management.db"
        )
        self.secret_key: str = os.getenv(
            "SECRET_KEY", "dev-secret-key-change-me-32bytes-minimum"
        )
        self.algorithm: str = os.getenv("ALGORITHM", "HS256")
        self.access_token_expire_minutes: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
        )
        self.allowed_hosts: list[str] = [
            h.strip()
            for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
            if h.strip()
        ]


settings = Settings()