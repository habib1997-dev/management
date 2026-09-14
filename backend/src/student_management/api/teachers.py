"""Teacher endpoints (admin-only management)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from student_management.api.deps import require_roles
from student_management.db import get_db
from student_management.models import User
from student_management.schemas.account import AccountCreate, AccountDetail, AccountResponse
from student_management.schemas.course import CourseSummary
from student_management.schemas.teacher import (
    TeacherCreate,
    TeacherDetail,
    TeacherListResponse,
    TeacherResponse,
    TeacherSummary,
    TeacherUpdate,
)
from student_management.services import account_service, teacher_service

router = APIRouter(prefix="/api/v1", tags=["teachers"])

admin_only = require_roles("admin")


@router.get("/teachers")
def list_teachers(
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
) -> TeacherListResponse:
    teachers = teacher_service.list_teachers(db)
    return TeacherListResponse(
        data=[TeacherSummary.model_validate(t) for t in teachers],
        meta={"total": len(teachers)},
    )


@router.post("/teachers", status_code=201)
def create_teacher(
    payload: TeacherCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
) -> TeacherResponse:
    teacher = teacher_service.create_teacher(db, payload)
    return TeacherResponse(
        teacher=TeacherDetail.model_validate(teacher),
        message="Teacher successfully created",
    )


@router.put("/teachers/{teacher_id}")
def update_teacher(
    teacher_id: str,
    payload: TeacherUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
) -> TeacherResponse:
    """Update a teacher's profile and/or active status (admin-only). Follows their login too."""
    teacher = teacher_service.get_teacher_or_404(db, teacher_id)
    teacher = teacher_service.update_teacher(db, teacher, payload)
    return TeacherResponse(
        teacher=TeacherDetail.model_validate(teacher),
        message="Teacher successfully updated",
    )


@router.get("/teachers/{teacher_id}")
def get_teacher(
    teacher_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
) -> TeacherDetail:
    teacher = teacher_service.get_teacher_with_courses(db, teacher_id)
    detail = TeacherDetail.model_validate(teacher)
    detail.courses = [CourseSummary.model_validate(c) for c in teacher.courses]
    return detail


@router.post(
    "/teachers/{teacher_id}/account", status_code=201
)
def create_teacher_account(
    teacher_id: str,
    payload: AccountCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
) -> AccountResponse:
    user = account_service.create_teacher_account(db, teacher_id, payload.password)
    return AccountResponse(
        account=AccountDetail(email=user.email, role=user.role, user_id=user.user_id),
        message="Teacher login created",
    )