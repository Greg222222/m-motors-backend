from app.models import Role, User
from app.security import verify_password
from scripts import create_admin as create_admin_module
from scripts.create_admin import main as create_admin
from tests.conftest import TestingSessionLocal


def test_create_admin_creates_a_new_admin_account(db_session, monkeypatch):
    monkeypatch.setattr(create_admin_module, "SessionLocal", TestingSessionLocal)
    create_admin("new-admin@m-motors.fr", "StrongPassword123")

    user = db_session.query(User).filter(User.email == "new-admin@m-motors.fr").first()
    assert user is not None
    assert user.role == Role.admin
    assert verify_password("StrongPassword123", user.hashed_password)


def test_create_admin_promotes_and_resets_password_for_existing_account(db_session, monkeypatch):
    monkeypatch.setattr(create_admin_module, "SessionLocal", TestingSessionLocal)
    user = User(email="client@m-motors.fr", hashed_password="irrelevant", role=Role.client)
    db_session.add(user)
    db_session.commit()

    create_admin("client@m-motors.fr", "NewPassword456")

    db_session.refresh(user)
    assert user.role == Role.admin
    assert verify_password("NewPassword456", user.hashed_password)
