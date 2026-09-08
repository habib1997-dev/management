"""Administrator endpoints (admin-only)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from student_management.api.deps import require_roles
from student_management.db import get_db
from student_management.models import User
from student_management.schemas.account import (
    UserAdminDetail,
    UserAdminResponse,
    UserAdminUpdate,
)
from student_management.services import account_service

router = APIRouter(prefix="/api/v1/administrators", tags=["administrators"])


@router.get("")
def list_administrators(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
) -> dict:
    admins = db.query(User).filter(User.role == "admin").all()
    return {
        "data": [
            {
                "admin_id": str(u.user_id),
                "name": u.email.split("@")[0],
                "email": u.email,
                "role": u.role,
                "status": u.active,
            }
            for u in admins
        ]
    }


@router.get("/users", response_model=dict)
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
) -> dict:
    users = account_service.list_users(db)
    return {
        "data": [UserAdminDetail.model_validate(u) for u in users],
        "meta": {"total": len(users)},
    }


@router.put("/users/{user_id}", response_model=UserAdminResponse)
def update_user(
    user_id: str,
    payload: UserAdminUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
) -> UserAdminResponse:
    """Deactivate/reactivate a login or reset its password (admin-only)."""
    user = account_service.get_user_or_404(db, user_id)
    user = account_service.update_user_account(
        db, user, password=payload.password, active=payload.active
    )
    messages = []
    if payload.active is not None:
        messages.append("activated" if payload.active else "deactivated")
    if payload.password is not None:
        messages.append("password reset")
    return UserAdminResponse(
        user=UserAdminDetail.model_validate(user),
        message=f"User {' and '.join(messages)}",
    )