def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def _create_vehicle(client, admin_token, mode="both"):
    response = client.post(
        "/vehicles",
        json={
            "brand": "Renault",
            "model": "Clio",
            "year": 2022,
            "mileage": 1000,
            "color": "Bleu",
            "fuel_type": "essence",
            "price_sale": 9000,
            "price_rent_monthly": 220,
            "mode": mode,
        },
        headers=auth_header(admin_token),
    )
    return response.json()["id"]


def test_client_can_create_dossier(client, client_token, admin_token):
    vehicle_id = _create_vehicle(client, admin_token)
    response = client.post(
        "/dossiers", json={"vehicle_id": vehicle_id, "type": "location"}, headers=auth_header(client_token)
    )
    assert response.status_code == 201
    assert response.json()["status"] == "en_attente"


def test_create_dossier_unknown_vehicle_returns_404(client, client_token):
    response = client.post(
        "/dossiers", json={"vehicle_id": 999, "type": "achat"}, headers=auth_header(client_token)
    )
    assert response.status_code == 404


def test_create_dossier_rejects_incompatible_type(client, client_token, admin_token):
    vehicle_id = _create_vehicle(client, admin_token, mode="rent")
    response = client.post(
        "/dossiers", json={"vehicle_id": vehicle_id, "type": "achat"}, headers=auth_header(client_token)
    )
    assert response.status_code == 422


def test_create_dossier_rejects_already_engaged_vehicle(client, client_token, admin_token):
    vehicle_id = _create_vehicle(client, admin_token)
    client.post("/dossiers", json={"vehicle_id": vehicle_id, "type": "achat"}, headers=auth_header(client_token))

    other_client = client.post("/auth/register", json={"email": "other@example.com", "password": "Password123"})
    assert other_client.status_code == 201
    other_token = client.post(
        "/auth/login", data={"username": "other@example.com", "password": "Password123"}
    ).json()["access_token"]

    response = client.post(
        "/dossiers", json={"vehicle_id": vehicle_id, "type": "achat"}, headers=auth_header(other_token)
    )
    assert response.status_code == 409


def test_client_sees_only_own_dossiers(client, client_token, admin_token):
    vehicle_id = _create_vehicle(client, admin_token)
    client.post("/dossiers", json={"vehicle_id": vehicle_id, "type": "achat"}, headers=auth_header(client_token))
    response = client.get("/dossiers/me", headers=auth_header(client_token))
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_non_admin_cannot_list_all_dossiers(client, client_token):
    response = client.get("/dossiers", headers=auth_header(client_token))
    assert response.status_code == 403


def test_admin_can_validate_dossier(client, client_token, admin_token):
    vehicle_id = _create_vehicle(client, admin_token)
    created = client.post(
        "/dossiers", json={"vehicle_id": vehicle_id, "type": "achat"}, headers=auth_header(client_token)
    )
    dossier_id = created.json()["id"]

    response = client.post(
        f"/dossiers/{dossier_id}/decision", json={"approve": True}, headers=auth_header(admin_token)
    )
    assert response.status_code == 200
    assert response.json()["status"] == "valide"


def test_refusal_requires_a_reason(client, client_token, admin_token):
    vehicle_id = _create_vehicle(client, admin_token)
    created = client.post(
        "/dossiers", json={"vehicle_id": vehicle_id, "type": "achat"}, headers=auth_header(client_token)
    )
    dossier_id = created.json()["id"]

    response = client.post(
        f"/dossiers/{dossier_id}/decision", json={"approve": False}, headers=auth_header(admin_token)
    )
    assert response.status_code == 422


def test_refusal_frees_the_vehicle_for_mode_switch(client, client_token, admin_token):
    vehicle_id = _create_vehicle(client, admin_token)
    created = client.post(
        "/dossiers", json={"vehicle_id": vehicle_id, "type": "location"}, headers=auth_header(client_token)
    )
    dossier_id = created.json()["id"]

    blocked = client.patch(f"/vehicles/{vehicle_id}/mode", json={"mode": "sale"}, headers=auth_header(admin_token))
    assert blocked.status_code == 409

    client.post(
        f"/dossiers/{dossier_id}/decision",
        json={"approve": False, "refusal_reason": "Dossier incomplet"},
        headers=auth_header(admin_token),
    )

    allowed = client.patch(f"/vehicles/{vehicle_id}/mode", json={"mode": "sale"}, headers=auth_header(admin_token))
    assert allowed.status_code == 200


def test_dossier_cannot_be_decided_twice(client, client_token, admin_token):
    vehicle_id = _create_vehicle(client, admin_token)
    created = client.post(
        "/dossiers", json={"vehicle_id": vehicle_id, "type": "achat"}, headers=auth_header(client_token)
    )
    dossier_id = created.json()["id"]
    client.post(f"/dossiers/{dossier_id}/decision", json={"approve": True}, headers=auth_header(admin_token))

    response = client.post(
        f"/dossiers/{dossier_id}/decision", json={"approve": True}, headers=auth_header(admin_token)
    )
    assert response.status_code == 409
