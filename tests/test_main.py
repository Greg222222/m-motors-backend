from fastapi.testclient import TestClient

from app import main as main_module
from app.database import get_db


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_unhandled_exception_returns_500_and_triggers_alert(monkeypatch):
    alerts = []
    monkeypatch.setattr(main_module, "send_alert", lambda title, detail: alerts.append((title, detail)) or True)

    def broken_db():
        raise RuntimeError("database is on fire")
        yield  # pragma: no cover

    previous_override = main_module.app.dependency_overrides[get_db]
    main_module.app.dependency_overrides[get_db] = broken_db
    try:
        # raise_server_exceptions=False so the TestClient returns the real
        # HTTP response produced by our global exception handler instead of
        # re-raising the exception (the default, developer-friendly behaviour).
        no_raise_client = TestClient(main_module.app, raise_server_exceptions=False)
        response = no_raise_client.get("/vehicles")
    finally:
        main_module.app.dependency_overrides[get_db] = previous_override

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert len(alerts) == 1
    assert "vehicles" in alerts[0][1]
