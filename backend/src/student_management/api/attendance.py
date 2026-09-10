"""Attendance endpoints (teachers for their own courses, admins for any)."""

from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from student_management.api.deps import assert_can_access_course, require_roles
from student_management.db import get_db
from student_management.models import User
from student_management.schemas.attendance import (
    AttendanceCreate,
    AttendanceDetail,
    AttendanceResponse,
)
from student_management.services import attendance_service, course_service

router = APIRouter(prefix="/api/v1", tags=["attendance"])

staff_only = require_roles("admin", "teacher")


@router.post("/attendance", response_model=AttendanceResponse, status_code=201)
def mark_attendance(
    payload: AttendanceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> AttendanceResponse:
    course = course_service.get_course_or_404(db, payload.course_id)
    assert_can_access_course(course, user)
    attendance = attendance_service.mark_attendance(db, payload, user.teacher_id)
    return AttendanceResponse(
        attendance=[AttendanceDetail.model_validate(a) for a in attendance],
        message="Attendance successfully recorded",
    )


@router.get("/attendance/{course_id}", response_model=dict)
def list_course_attendance(
    course_id: str,
    date: date_type | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> dict:
    course = course_service.get_course_or_404(db, course_id)
    assert_can_access_course(course, user)
    records = attendance_service.list_course_attendance(db, course_id, date)
    return {
        "data": [AttendanceDetail.model_validate(r) for r in records],
        "meta": {"total": len(records)},
    }


@router.get("/students/{student_id}/attendance", response_model=dict)
def get_student_attendance(
    student_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> dict:
    attendance_service.get_student_or_404(db, student_id)
    if user.role == "teacher":
        if not attendance_service.student_in_teacher_courses(
            db, student_id, user.teacher_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view attendance for your own students",
            )
        own_course_ids = course_service.list_teacher_course_ids(
            db, user.teacher_id
        )
        records = attendance_service.list_student_attendance(
            db, student_id, course_ids=own_course_ids
        )
    else:
        records = attendance_service.list_student_attendance(db, student_id)
    return {
        "data": [AttendanceDetail.model_validate(r) for r in records],
        "meta": {"total": len(records)},
    }