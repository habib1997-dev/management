"""Authentication endpoints: login and token issuance."""

import threading
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from student_management.db import get_db
from student_management.models import User
from student_management.schemas.auth import LoginRequest, LoginResponse
from student_management.security import create_access_token, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

MAX_FAILED_LOGINS = 5
LOGIN_WINDOW_SECONDS = 15 * 60

# Pre-computed bcrypt hash so failed logins for unknown email addresses still
# spend the same amount of time hashing as real lookups (uniform timing).
_DUMMY_HASH = (
    "$2b$12$81dulMRfNQI77qPr47HmqOpnKNMigChkRLIvaITgzAvdPYbKkrmqu"
)

_LOCK = threading.Lock()
_FAILURES: dict[str, deque[float]] = defaultdict(deque)


def _key(email: str, host: str) -> str:
    return f"{email.strip().lower()}|{host}"


def _is_throttled(key: str) -> bool:
    now = time.monotonic()
    with _LOCK:
        history = _FAILURES[key]
        while history and now - history[0] > LOGIN_WINDOW_SECONDS:
            history.popleft()
        return len(history) >= MAX_FAILED_LOGINS


def _record_failure(key: str) -> None:
    with _LOCK:
        _FAILURES[key].append(time.monotonic())


def _clear_failures(key: str) -> None:
    with _LOCK:
        _FAILURES.pop(key, None)


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """Authenticate a user with email/password and return a JWT bearer token.

    Login attempts are throttled in-memory per email+client-IP: after 5 failed
    attempts within 15 minutes the endpoint returns 429. This is fine for a
    single-process deployment; multi-instance setups should key the counter off
    a shared store (e.g. Redis) and only trust ``X-Forwarded-For`` when running
    behind a reverse proxy.
    """
    host = request.client.host if request.client else ""
    key = _key(payload.email, host)
    if _is_throttled(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again in 15 minutes.",
        )

    user = db.query(User).filter(func.lower(User.email) == payload.email.lower()).first()
    valid = user is not None and user.active and verify_password(
        payload.password, user.password_hash
    )
    if not valid:
        if user is None or not user.active:
            verify_password(payload.password, _DUMMY_HASH)
        _record_failure(key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    _clear_failures(key)
    return LoginResponse(
        access_token=create_access_token(user),
        role=user.role,
        user_id=str(user.user_id),
        email=user.email,
        teacher_id=user.teacher_id,
        parent_id=user.parent_id,
    )