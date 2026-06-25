def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def _create_vehicle(client, admin_token):
    response = client.post(
        "/vehicles",
        json={
            "brand": "Renault",
            "model": "Clio",
            "mileage": 1000,
            "price_sale": 9000,
            "price_rent_monthly": 220,
            "mode": "both",
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


def test_client_sees_only_own_dossiers(client, client_token, admin_token):
    vehicle_id = _create_vehicle(client, admin_token)
    client.post("/dossiers", json={"vehicle_id": vehicle_id, "type": "achat"}, headers=auth_header(client_token))
    response = client.get("/dossiers/me", headers=auth_header(client_token))
    assert response.status_code == 200
    assert len(response.json()) == 1
