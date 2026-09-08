"""Student endpoints: enroll, list, search, view, update; and enrollments."""

from fastapi import APIRouter, Depends, Query
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


@router.post("/students", response_model=StudentResponse, status_code=201)
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


@router.get("/students", response_model=StudentListResponse)
def list_students(
    db: Session = Depends(get_db),
    _admin: User = Depends(staff_only),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    search: str | None = None,
    gradeLevel: str | None = None,
    active: bool | None = None,
) -> StudentListResponse:
    items, total = student_service.list_students(
        db, page=page, page_size=pageSize, search=search, grade_level=gradeLevel, active=active
    )
    return StudentListResponse(
        data=[StudentDetail.model_validate(s) for s in items],
        meta={"page": page, "pageSize": pageSize, "total": total},
    )


@router.get("/students/{student_id}", response_model=StudentDetail)
def get_student(
    student_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(staff_only),
) -> StudentDetail:
    student = student_service.get_student_or_404(db, student_id)
    return StudentDetail.model_validate(student)


@router.put("/students/{student_id}", response_model=StudentResponse)
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


@router.post("/enrollments", response_model=EnrollmentResponse, status_code=201)
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


@router.get("/students/{student_id}/parents", response_model=dict)
def list_student_parents(
    student_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
) -> dict:
    """All parents linked to a student (admin-only)."""
    parents = parent_service.list_student_parents(db, student_id)
    return {
        "data": [ParentSummary.model_validate(p) for p in parents],
        "meta": {"total": len(parents)},
    }