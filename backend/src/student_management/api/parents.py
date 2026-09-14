"""Parent endpoints (admin-only management plus parent portal)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from student_management.api.deps import require_roles
from student_management.db import get_db
from student_management.models import Course, User
from student_management.schemas.account import AccountCreate, AccountDetail, AccountResponse
from student_management.schemas.attendance import AttendanceDetail
from student_management.schemas.grade import GradeDetail
from student_management.schemas.parent import (
    ParentCreate,
    ParentListResponse,
    ParentPortal,
    ParentResponse,
    ParentStudentsUpdate,
    ParentSummary,
    ParentUpdate,
    PortalChild,
    PortalParent,
)
from student_management.schemas.student import StudentSummary
from student_management.services import account_service, parent_service

router = APIRouter(prefix="/api/v1", tags=["parents"])

admin_only = require_roles("admin")
parent_only = require_roles("parent")


@router.get("/parents")
def list_parents(
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
) -> ParentListResponse:
    parents = parent_service.list_parents(db)
    return ParentListResponse(
        data=[ParentSummary.model_validate(p) for p in parents],
        meta={"total": len(parents)},
    )


@router.post("/parents", status_code=201)
def create_parent(
    payload: ParentCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
) -> ParentResponse:
    parent = parent_service.create_parent(db, payload)
    return ParentResponse(
        parent=ParentSummary.model_validate(parent),
        message="Parent successfully created",
    )


@router.put("/parents/{parent_id}")
def update_parent(
    parent_id: str,
    payload: ParentUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
) -> ParentResponse:
    """Update a parent's profile and/or active status (admin-only). Follows their login too."""
    parent = parent_service.get_parent_or_404(db, parent_id)
    parent = parent_service.update_parent(db, parent, payload)
    return ParentResponse(
        parent=ParentSummary.model_validate(parent),
        message="Parent successfully updated",
    )


@router.get("/parents/{parent_id}/students")
def list_parent_students(
    parent_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
) -> dict:
    students = parent_service.list_parent_students(db, parent_id)
    return {
        "data": [StudentSummary.model_validate(s) for s in students],
        "meta": {"total": len(students)},
    }


@router.put("/parents/{parent_id}/students")
def update_parent_students(
    parent_id: str,
    payload: ParentStudentsUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
) -> dict:
    """Replace the students linked to this parent (admin-only)."""
    parent = parent_service.get_parent_or_404(db, parent_id)
    parent = parent_service.update_parent_students(db, parent, payload.student_ids)
    return {
        "data": [StudentSummary.model_validate(s) for s in parent.students],
        "meta": {"total": len(parent.students)},
        "message": "Parent's students updated",
    }


@router.post(
    "/parents/{parent_id}/account", status_code=201
)
def create_parent_account(
    parent_id: str,
    payload: AccountCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
) -> AccountResponse:
    user = account_service.create_parent_account(db, parent_id, payload.password)
    return AccountResponse(
        account=AccountDetail(email=user.email, role=user.role, user_id=user.user_id),
        message="Parent login created",
    )


@router.get("/parents/{parent_id}/portal")
def get_parent_portal(
    parent_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(parent_only),
) -> ParentPortal:
    try:
        requested_id = uuid.UUID(str(parent_id).strip())
    except ValueError:
        requested_id = None
    if user.parent_id is None or requested_id != user.parent_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own portal",
        )
    parent = parent_service.get_parent_with_children(db, parent_id)
    if not parent.status:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parent account is deactivated",
        )
    course_ids = {
        *(a.course_id for student in parent.students for a in student.attendance_records),
        *(g.course_id for student in parent.students for g in student.grades),
    }
    course_names: dict[uuid.UUID, str] = {}
    if course_ids:
        course_names = dict(
            db.query(Course.course_id, Course.name)
            .filter(Course.course_id.in_(course_ids))
            .all()
        )
    children = [
        PortalChild(
            student_id=student.student_id,
            first_name=student.first_name,
            last_name=student.last_name,
            grade_level=student.grade_level,
            attendance=[
                AttendanceDetail.model_validate(a).model_copy(
                    update={"course_name": course_names.get(a.course_id)}
                )
                for a in student.attendance_records
            ],
            grades=[
                GradeDetail.model_validate(g).model_copy(
                    update={"course_name": course_names.get(g.course_id)}
                )
                for g in student.grades
            ],
        )
        for student in parent.students
    ]
    return ParentPortal(
        parents=[
            PortalParent(
                parent_id=parent.parent_id,
                name=parent.name,
                email=parent.email,
                children=children,
            )
        ]
    )