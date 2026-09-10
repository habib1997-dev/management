"""Public school-branding endpoints (no authentication required)."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from student_management.services.school_profile import (
    BrandingError,
    get_branding,
    logo_media_type,
    logo_path,
)

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


@router.get("/brand")
def get_school_brand() -> dict:
    try:
        return get_branding()
    except BrandingError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/brand/logo")
def get_school_logo() -> FileResponse:
    path = logo_path()
    if path is None:
        raise HTTPException(status_code=404, detail="No school logo is configured.")
    return FileResponse(path, media_type=logo_media_type())