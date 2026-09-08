"""Report endpoints: report-card PDF export."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from student_management.api.deps import require_roles
from student_management.db import get_db
from student_management.models import User
from student_management.services import attendance_service, report_service

router = APIRouter(prefix="/api/v1", tags=["reports"])

staff_only = require_roles("admin", "teacher")


@router.get("/reports/{student_id}", response_model=None)
def generate_report_card(
    student_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
) -> Response:
    student = attendance_service.get_student_or_404(db, student_id)
    if (
        user.role == "teacher"
        and not attendance_service.student_in_teacher_courses(
            db, student_id, user.teacher_id
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view reports for your own students",
        )

    pdf_bytes = report_service.build_pdf(db, student_id)
    filename = f"report_card_{student.last_name}_{student.first_name}.pdf"
    return Response(
        content=pdf_bytes,
        media_type=report_service.REPORT_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )