import uuid

import pytest
import student_management.models  # noqa: F401 - register tables on Base.metadata
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from student_management.db import Base, get_db
from student_management.main import app
from student_management.models import User
from student_management.security import create_access_token, hash_password


@pytest.fixture
def db_session() -> Session:
    # StaticPool keeps ONE shared connection across threads so the TestClient's
    # worker thread sees the same in-memory database.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def make_auth_headers(db_session: Session):
    """Factory producing Authorization headers for a given role/email."""

    def _make(
        email: str | None = None,
        role: str = "admin",
        teacher_id=None,
        parent_id=None,
    ) -> dict[str, str]:
        email = email or f"{role}@test.edu"
        user = db_session.query(User).filter(User.email == email).first()
        if user is None:
            user = User(
                email=email,
                password_hash=hash_password("password123"),
                role=role,
                teacher_id=uuid.UUID(str(teacher_id)) if teacher_id else None,
                parent_id=uuid.UUID(str(parent_id)) if parent_id else None,
            )
            db_session.add(user)
            db_session.commit()
        token = create_access_token(user)
        return {"Authorization": f"Bearer {token}"}

    return _make


@pytest.fixture
def client(db_session: Session) -> TestClient:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # Plain TestClient (no context manager): startup lifespan is not triggered,
    # so the on-disk dev database is not created during tests.
    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()
        client.close()