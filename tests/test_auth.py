def test_register_creates_user(client):
    response = client.post("/auth/register", json={"email": "new@example.com", "password": "Password123"})
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert body["role"] == "client"


def test_register_duplicate_email_rejected(client):
    client.post("/auth/register", json={"email": "dup@example.com", "password": "Password123"})
    response = client.post("/auth/register", json={"email": "dup@example.com", "password": "Password123"})
    assert response.status_code == 409


def test_login_success_returns_token(client):
    client.post("/auth/register", json={"email": "login@example.com", "password": "Password123"})
    response = client.post("/auth/login", data={"username": "login@example.com", "password": "Password123"})
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert len(response.json()["access_token"]) > 10


def test_login_wrong_password_rejected(client):
    client.post("/auth/register", json={"email": "wrong@example.com", "password": "Password123"})
    response = client.post("/auth/login", data={"username": "wrong@example.com", "password": "BadPassword"})
    assert response.status_code == 401


def test_login_unknown_user_rejected(client):
    response = client.post("/auth/login", data={"username": "ghost@example.com", "password": "whatever"})
    assert response.status_code == 401


def test_protected_endpoint_requires_token(client):
    response = client.get("/dossiers/me")
    assert response.status_code == 401


def test_protected_endpoint_rejects_invalid_token(client):
    response = client.get("/dossiers/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401
