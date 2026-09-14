"""Student endpoints: enroll, list, search, view, update; and enrollments."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from student_management.api.deps import require_roles
from student_management.db import get_db
from student_management.models import User
from student_management.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentDetail,
    EnrollmentResponse,
)
from student_management.schemas.parent import ParentSummary
from student_management.schemas.student import (
    StudentDetail,
    StudentEnrollment,
    StudentListResponse,
    StudentResponse,
    StudentUpdate,
)
from student_management.services import parent_service, student_service

router = APIRouter(prefix="/api/v1", tags=["students"])

admin_only = require_roles("admin")
staff_only = require_roles("admin", "teacher")


def _student_detail(detail: StudentDetail, *, redact_contact: bool) -> StudentDetail:
    """Mask a student's personal contact info for non-admin roles.

    Student email/phone are admin-only; teachers keep the profile but on a
    need-to-know basis (names, grade level, dates) without contact details.
    """
    if redact_contact:
        detail.email = None
        detail.phone = None
    return detail


@router.post("/students", status_code=201)
def enroll_student(
    payload: StudentEnrollment,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_only),
) -> StudentResponse:
    student = student_service.create_student(db, payload, enrolled_by=admin.email)
    return StudentResponse(
        student=StudentDetail.model_validate(student),
        message="Student successfully enrolled",
    )


@router.get("/students")
def list_students(
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    search: str | None = None,
    grade_level: str | None = Query(default=None, alias="gradeLevel"),
    active: bool | None = None,
) -> StudentListResponse:
    own_teacher_id = user.teacher_id if user.role == "teacher" else None
    items, total = student_service.list_students(
        db,
        page=page,
        page_size=page_size,
        search=search,
        grade_level=grade_level,
        active=active,
        own_teacher_id=own_teacher_id,
    )
    return StudentListResponse(
        data=[
            _student_detail(StudentDetail.model_validate(s), redact_contact=user.role != "admin")
            for s in items
        ],
        meta={"page": page, "pageSize": page_size, "total": total},
    )


@router.get("/students/{student_id}")
def get_student(
    student_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> StudentDetail:
    if user.role == "teacher":
        student = student_service.get_student_for_teacher(db, student_id, user.teacher_id)
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view profiles of the students you teach",
            )
    else:
        student = student_service.get_student_or_404(db, student_id)
    return _student_detail(StudentDetail.model_validate(student), redact_contact=user.role != "admin")


@router.put("/students/{student_id}")
def update_student(
    student_id: str,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_only),
) -> StudentResponse:
    student = student_service.get_student_or_404(db, student_id)
    student = student_service.update_student(db, student, payload)
    return StudentResponse(
        student=StudentDetail.model_validate(student),
        message="Student successfully updated",
    )


@router.post("/enrollments", status_code=201)
def create_enrollment(
    payload: EnrollmentCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
) -> EnrollmentResponse:
    enrollment = student_service.create_enrollment(db, payload)
    return EnrollmentResponse(
        enrollment=EnrollmentDetail.model_validate(enrollment),
        message="Enrollment successfully created",
    )


@router.get("/students/{student_id}/parents")
def list_student_parents(
    student_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> dict:
    """Parents linked to a student.

    Admins can look up any student. Teachers can only look up students they
    teach (the same "own courses" scope used for profiles) so they can reach a
    guardian about absences or poor performance. Parents have the portal for
    their own children and no access to other people's records.
    """
    if user.role == "teacher":
        student = student_service.get_student_for_teacher(db, student_id, user.teacher_id)
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view parents of the students you teach",
            )
    parents = parent_service.list_student_parents(db, student_id)
    return {
        "data": [ParentSummary.model_validate(p) for p in parents],
        "meta": {"total": len(parents)},
    }