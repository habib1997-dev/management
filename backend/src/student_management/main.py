"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from student_management.api import (
    administrators,
    attendance,
    auth,
    courses,
    grades,
    parents,
    reports,
    students,
    teachers,
)
from student_management.db import Base, engine


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create tables on startup for development convenience.

    Production deployments use Alembic migrations instead (see alembic/).
    """
    import student_management.models  # noqa: F401 - registers all tables

    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Student Management System API",
    description="REST API for student enrollment, attendance, grades, courses, parents, and reports.",
    version="1.0.0",
    lifespan=lifespan,
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


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}