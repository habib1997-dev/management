"""Single source of truth for school branding.

Both the public branding endpoint (``api.school_profile``) and the report-card
PDF generator (``services.report_service``) read from this module, so the web
app and the printed reports always show the same school name, colours and logo.

The logo file lives in a controlled ``static/branding`` folder; the configured
value is only a plain filename (validated here: no directory separators, no
path traversal, extension whitelist). A setting can never point at an
arbitrary file on the server.
"""

from pathlib import Path

from student_management.config import settings

BRANDING_DIR = Path(__file__).resolve().parent.parent / "static" / "branding"
ALLOWED_LOGO_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
LOGO_MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


class BrandingError(RuntimeError):
    """Raised when school branding is misconfigured."""


def _validate_logo_filename(filename: str) -> str:
    """Return the safe basename for the configured logo, or raise."""
    name = filename.strip()
    if not name:
        return ""
    if "/" in name or "\\" in name or name in {".", ".."}:
        raise BrandingError(
            f"School logo must be a plain filename inside the branding folder, "
            f"got {filename!r}."
        )
    if Path(name).suffix.lower() not in ALLOWED_LOGO_EXTENSIONS:
        raise BrandingError(
            f"School logo must be one of {sorted(ALLOWED_LOGO_EXTENSIONS)}, "
            f"got {filename!r}."
        )
    return name


def logo_path() -> Path | None:
    """Return the resolved path to the logo file, or ``None`` if unset.

    Raises :class:`BrandingError` if the configured file is missing or the
    filename is unsafe.
    """
    name = _validate_logo_filename(settings.school_logo_filename)
    if not name:
        return None
    path = BRANDING_DIR / name
    if not path.is_file():
        raise BrandingError(
            f"Configured school logo {name!r} not found in {BRANDING_DIR}."
        )
    return path


def logo_media_type() -> str:
    """MIME type for the configured logo, derived from its file extension.

    Raises :class:`BrandingError` if the filename is unsafe or not whitelisted.
    """
    name = Path(_validate_logo_filename(settings.school_logo_filename))
    return LOGO_MEDIA_TYPES[name.suffix.lower()]


def get_branding() -> dict:
    """Return the public branding profile consumed by the web app."""
    logo = logo_path()
    return {
        "name": settings.school_name,
        "tagline": settings.school_tagline,
        "primary_color": settings.brand_primary,
        "secondary_color": settings.brand_secondary,
        "demo": settings.brand_demo,
        "logo_url": "/api/v1/settings/brand/logo" if logo else None,
    }