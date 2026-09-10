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