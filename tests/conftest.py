import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["RATE_LIMIT_LOGIN"] = "1000/minute"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Role, User
from app.security import hash_password

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def _fresh_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def admin_token(client, db_session):
    admin = User(email="admin@m-motors.fr", hashed_password=hash_password("AdminPass123"), role=Role.admin)
    db_session.add(admin)
    db_session.commit()
    response = client.post(
        "/auth/login", data={"username": "admin@m-motors.fr", "password": "AdminPass123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def client_token(client):
    client.post("/auth/register", json={"email": "client@example.com", "password": "ClientPass123"})
    response = client.post(
        "/auth/login", data={"username": "client@example.com", "password": "ClientPass123"}
    )
    return response.json()["access_token"]
