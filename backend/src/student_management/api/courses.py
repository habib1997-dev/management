"""Course endpoints (admin management, teacher read for own courses)."""


from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from student_management.api.deps import assert_can_access_course, require_roles
from student_management.db import get_db
from student_management.models import User
from student_management.schemas.course import (
    CourseCreate,
    CourseDetail,
    CourseListResponse,
    CourseResponse,
    CourseRosterUpdate,
    CourseSummary,
    CourseUpdate,
)
from student_management.schemas.parent import ParentSummary
from student_management.schemas.student import StudentSummary
from student_management.services import course_service

router = APIRouter(prefix="/api/v1", tags=["courses"])

admin_only = require_roles("admin")
staff_only = require_roles("admin", "teacher")


@router.get("/courses")
def list_courses(
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
    teacher_id: str | None = Query(default=None, alias="teacherId"),
    grade_level: str | None = Query(default=None, alias="gradeLevel"),
) -> CourseListResponse:
    own_teacher_id = user.teacher_id if user.role == "teacher" else None
    courses = course_service.list_courses(
        db,
        teacher_id=teacher_id,
        grade_level=grade_level,
        own_teacher_id=own_teacher_id,
    )
    return CourseListResponse(
        data=[CourseSummary.model_validate(c) for c in courses],
        meta={"total": len(courses)},
    )


@router.post("/courses", status_code=201)
def create_course(
    payload: CourseCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
) -> CourseResponse:
    course = course_service.create_course(db, payload)
    return CourseResponse(
        course=CourseDetail.model_validate(course),
        message="Course successfully created",
    )


@router.get("/courses/{course_id}")
def get_course(
    course_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> CourseDetail:
    course = course_service.get_course_with_reads(db, course_id)
    assert_can_access_course(course, user)
    detail = CourseDetail.model_validate(course)
    detail.students = [StudentSummary.model_validate(s) for s in course.students]
    return detail


@router.put("/courses/{course_id}")
def update_course(
    course_id: str,
    payload: CourseUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_only),
) -> CourseResponse:
    course = course_service.get_course_or_404(db, course_id)
    course = course_service.update_course(db, course, payload)
    return CourseResponse(
        course=CourseDetail.model_validate(course),
        message="Course successfully updated",
    )


@router.get("/courses/{course_id}/students")
def list_course_students(
    course_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> dict:
    course = course_service.get_course_or_404(db, course_id)
    assert_can_access_course(course, user)
    students = course_service.list_course_students(db, course_id)
    return {
        "data": [StudentSummary.model_validate(s) for s in students],
        "meta": {"total": len(students)},
    }


@router.get("/courses/{course_id}/parents")
def list_course_parents(
    course_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> dict:
    """Parents of the students in a course, grouped per student.

    A teacher can view this for their own courses so they can reach guardians
    about absences or poor performance; admins for any course.
    """
    course = course_service.get_course_or_404(db, course_id)
    assert_can_access_course(course, user)
    students = course_service.list_course_students(db, course_id)
    parents_by_student = course_service.parents_by_student(
        db, [s.student_id for s in students]
    )
    data = [
        {
            "student_id": str(s.student_id),
            "student_name": f"{s.first_name} {s.last_name}",
            "parents": [
                ParentSummary.model_validate(p) for p in parents_by_student.get(s.student_id, [])
            ],
        }
        for s in students
    ]
    return {"data": data, "meta": {"total": len(students)}}


@router.put("/courses/{course_id}/students")
def update_course_students(
    course_id: str,
    payload: CourseRosterUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
) -> CourseDetail:
    """Replace the roster of students assigned to this course (admin-only)."""
    course = course_service.get_course_or_404(db, course_id)
    course = course_service.assign_course_students(db, course, payload.student_ids)
    detail = CourseDetail.model_validate(course)
    detail.students = [StudentSummary.model_validate(s) for s in course.students]
    return detail