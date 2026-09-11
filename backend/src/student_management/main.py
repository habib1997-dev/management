"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from student_management.api import (
    administrators,
    attendance,
    auth,
    courses,
    exports,
    grades,
    parents,
    reports,
    school_profile,
    students,
    teachers,
)
from student_management.config import settings
from student_management.db import Base, engine
from student_management.services.school_profile import BrandingError, logo_path


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create tables on startup for development convenience.

    Production deployments use Alembic migrations instead (see alembic/), so
    ``create_all`` is only run when ``APP_ENV`` is not ``prod``.
    """
    if settings.app_env != "prod":
        import student_management.models  # noqa: F401 - registers all tables

        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Student Management System API",
    description="REST API for student enrollment, attendance, grades, courses, parents, and reports.",
    version="1.0.0",
    lifespan=lifespan,
)

if settings.app_env == "prod":
    from starlette.middleware.trustedhost import TrustedHostMiddleware

    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts
    )

app.include_router(auth.router)
app.include_router(administrators.router)
app.include_router(students.router)
app.include_router(teachers.router)
app.include_router(courses.router)
app.include_router(attendance.router)
app.include_router(grades.router)
app.include_router(parents.router)
app.include_router(reports.router)
app.include_router(school_profile.router)
app.include_router(exports.router)

# Refuse to start with broken branding: a missing or unsafe logo file must be
# fixed before the app runs, so the web app and PDFs never show a broken crest.
try:
    logo_path()
except BrandingError as exc:
    raise RuntimeError(f"Invalid school branding: {exc}") from exc


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def serve_frontend(app: FastAPI) -> None:
    """Mount the React SPA if a built ``dist/`` directory is available.

    In development ``frontend/dist`` may not exist (you run ``npm run dev``
    instead).  The helper silently does nothing in that case.

    Set the ``FRONTEND_DIST`` environment variable to override the default
    path (``<repo>/frontend/dist``).
    """
    import os
    from pathlib import Path

    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import FileResponse
    from starlette.staticfiles import StaticFiles

    dist = Path(os.environ.get(
        "FRONTEND_DIST",
        str(Path(__file__).resolve().parents[4] / "frontend" / "dist"),
    ))
    if not dist.is_dir():
        return
    index = dist / "index.html"
    if not index.is_file():
        return

    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="frontend-assets")

    _index_path = str(index)

    class _SPA(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            if (
                response.status_code == 404
                and request.method == "GET"
                and not request.url.path.startswith("/api")
            ):
                return FileResponse(_index_path)
            return response

    app.add_middleware(_SPA)


serve_frontend(app)