"""Parent endpoints (admin-only management plus parent portal)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from student_management.api.deps import require_roles
from student_management.db import get_db
from student_management.models import User
from student_management.schemas.account import AccountCreate, AccountDetail, AccountResponse
from student_management.schemas.attendance import AttendanceDetail
from student_management.schemas.grade import GradeDetail
from student_management.schemas.parent import (
    ParentCreate,
    ParentListResponse,
    ParentPortal,
    ParentResponse,
    ParentSummary,
    PortalChild,
    PortalParent,
)
from student_management.schemas.student import StudentSummary
from student_management.services import account_service, parent_service

router = APIRouter(prefix="/api/v1", tags=["parents"])

admin_only = require_roles("admin")
parent_only = require_roles("parent")


@router.get("/parents", response_model=ParentListResponse)
def list_parents(
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
) -> ParentListResponse:
    parents = parent_service.list_parents(db)
    return ParentListResponse(
        data=[ParentSummary.model_validate(p) for p in parents],
        meta={"total": len(parents)},
    )


@router.post("/parents", response_model=ParentResponse, status_code=201)
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


@router.get("/parents/{parent_id}/students", response_model=dict)
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


@router.post(
    "/parents/{parent_id}/account", response_model=AccountResponse, status_code=201
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


@router.get("/parents/{parent_id}/portal", response_model=ParentPortal)
def get_parent_portal(
    parent_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(parent_only),
) -> ParentPortal:
    parent = parent_service.get_parent_with_children(db, parent_id)
    if user.parent_id is None or user.parent_id != parent.parent_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own portal",
        )
    children = [
        PortalChild(
            student_id=student.student_id,
            first_name=student.first_name,
            last_name=student.last_name,
            grade_level=student.grade_level,
            attendance=[AttendanceDetail.model_validate(a) for a in student.attendance_records],
            grades=[GradeDetail.model_validate(g) for g in student.grades],
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