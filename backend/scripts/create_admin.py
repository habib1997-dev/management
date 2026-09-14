"""One-time bootstrap for the FIRST production admin account.

The production Docker command never seeds demo data, so a real admin must be
created exactly once.  Run this from the deployed service shell (Render Shell):

    ADMIN_EMAIL=you@school.org ADMIN_PASSWORD='a long private passphrase' \
        python -m scripts.create_admin

If the variables are missing it prompts interactively.  Safety rules:

- the password must be at least 12 characters and may not be the demo default
  ``changeme123`` (refused on purpose);
- if an account with that email already exists the script exits successfully
  WITHOUT touching its password, so re-runs are safe.

Exit codes: 0 = ok; 1 = password/email policy failure; 2 = nothing to do
(no env vars and not interactive).
"""

from __future__ import annotations

import getpass
import os
import sys

from student_management.db import SessionLocal
from student_management.models import User
from student_management.security import hash_password

KNOWN_DEFAULT_PASSWORD = "changeme123"
MIN_PASSWORD_LENGTH = 12


def _read_env_or_prompt(name: str, secret: bool = False, prompt: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value is not None and value.strip():
        return value.strip()
    if not sys.stdin.isatty():
        return None
    try:
        if secret:
            return (getpass.getpass(prompt or f"{name}: ") or "").strip()
        return (input(prompt or f"{name}: ") or "").strip()
    except EOFError:
        return None


def _password_ok(password: str) -> bool:
    return len(password) >= MIN_PASSWORD_LENGTH and password.lower() != KNOWN_DEFAULT_PASSWORD


def main() -> int:
    email = _read_env_or_prompt("ADMIN_EMAIL", prompt="Admin email: ")
    password = None
    if email:
        password = _read_env_or_prompt("ADMIN_PASSWORD", secret=True, prompt="Admin password (hidden): ")

    if not email or not password:
        print("Set ADMIN_EMAIL and ADMIN_PASSWORD (or run interactively) to create the first admin.")
        return 2

    if not _password_ok(password):
        print(f"Password rejected: use at least {MIN_PASSWORD_LENGTH} characters and not the demo default.")
        return 1

    with SessionLocal() as session:
        existing = (
            session.query(User)
            .filter(User.email == email.lower())
            .first()
        )
        if existing is not None:
            print(f"Admin account already exists: {existing.email} (password left unchanged).")
            return 0

        admin = User(
            email=email.lower(),
            password_hash=hash_password(password),
            role="admin",
        )
        session.add(admin)
        session.commit()
        print(f"Created admin account: {admin.email}")
    return 0


if __name__ == "__main__":
    sys.exit(main())