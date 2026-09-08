"""Grade endpoints (teachers for their own courses, admins for any)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from student_management.api.deps import assert_can_access_course, require_roles
from student_management.db import get_db
from student_management.models import User
from student_management.schemas.grade import GradeCreate, GradeDetail, GradeResponse
from student_management.services import attendance_service, course_service, grade_service

router = APIRouter(prefix="/api/v1", tags=["grades"])

staff_only = require_roles("admin", "teacher")


@router.post("/grades", response_model=GradeResponse, status_code=201)
def record_grade(
    payload: GradeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> GradeResponse:
    course = course_service.get_course_or_404(db, payload.course_id)
    assert_can_access_course(course, user)
    grade = grade_service.record_grade(db, payload, user.teacher_id)
    return GradeResponse(
        grade=GradeDetail.model_validate(grade),
        message="Grade successfully recorded",
    )


@router.get("/students/{student_id}/grades", response_model=dict)
def get_student_grades(
    student_id: str,
    courseId: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> dict:
    attendance_service.get_student_or_404(db, student_id)
    if (
        user.role == "teacher"
        and not attendance_service.student_in_teacher_courses(
            db, student_id, user.teacher_id
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view grades for your own students",
        )
    records = grade_service.list_student_grades(db, student_id, courseId)
    return {
        "data": [GradeDetail.model_validate(r) for r in records],
        "meta": {"total": len(records)},
    }


@router.get("/courses/{course_id}/grades", response_model=dict)
def get_course_grades(
    course_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> dict:
    course = course_service.get_course_or_404(db, course_id)
    assert_can_access_course(course, user)
    records = grade_service.list_course_grades(db, course_id)
    return {
        "data": [GradeDetail.model_validate(r) for r in records],
        "meta": {"total": len(records)},
    }