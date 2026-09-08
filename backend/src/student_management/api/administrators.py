"""Administrator endpoints (admin-only)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from student_management.api.deps import require_roles
from student_management.db import get_db
from student_management.models import User

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