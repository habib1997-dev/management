"""Authentication endpoints: login and token issuance."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from student_management.db import get_db
from student_management.models import User
from student_management.schemas.auth import LoginRequest, LoginResponse
from student_management.security import create_access_token, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """Authenticate a user with email/password and return a JWT bearer token."""
    user = db.query(User).filter(func.lower(User.email) == payload.email.lower()).first()
    if user is None or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return LoginResponse(
        access_token=create_access_token(user),
        role=user.role,
        user_id=str(user.user_id),
        email=user.email,
    )