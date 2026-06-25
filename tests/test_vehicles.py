def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_create_vehicle_requires_admin(client, client_token):
    response = client.post(
        "/vehicles",
        json={"brand": "Renault", "model": "Clio", "mileage": 10000, "price_sale": 9000, "mode": "sale"},
        headers=auth_header(client_token),
    )
    assert response.status_code == 403


def test_admin_can_create_vehicle_for_sale(client, admin_token):
    response = client.post(
        "/vehicles",
        json={"brand": "Renault", "model": "Clio", "mileage": 10000, "price_sale": 9000, "mode": "sale"},
        headers=auth_header(admin_token),
    )
    assert response.status_code == 201
    assert response.json()["mode"] == "sale"


def test_create_vehicle_for_rent_requires_monthly_price(client, admin_token):
    response = client.post(
        "/vehicles",
        json={"brand": "Peugeot", "model": "208", "mileage": 5000, "mode": "rent"},
        headers=auth_header(admin_token),
    )
    assert response.status_code == 422


def test_list_vehicles_filters_by_mode(client, admin_token):
    client.post(
        "/vehicles",
        json={"brand": "Renault", "model": "Clio", "mileage": 1000, "price_sale": 9000, "mode": "sale"},
        headers=auth_header(admin_token),
    )
    client.post(
        "/vehicles",
        json={
            "brand": "Peugeot",
            "model": "208",
            "mileage": 2000,
            "price_rent_monthly": 250,
            "mode": "rent",
        },
        headers=auth_header(admin_token),
    )
    response = client.get("/vehicles", params={"mode": "rent"})
    assert response.status_code == 200
    brands = [v["brand"] for v in response.json()]
    assert brands == ["Peugeot"]


def test_toggle_vehicle_mode(client, admin_token):
    create = client.post(
        "/vehicles",
        json={
            "brand": "Citroen",
            "model": "C3",
            "mileage": 3000,
            "price_sale": 8000,
            "price_rent_monthly": 200,
            "mode": "sale",
        },
        headers=auth_header(admin_token),
    )
    vehicle_id = create.json()["id"]
    response = client.patch(
        f"/vehicles/{vehicle_id}/mode", json={"mode": "rent"}, headers=auth_header(admin_token)
    )
    assert response.status_code == 200
    assert response.json()["mode"] == "rent"


def test_toggle_mode_on_unknown_vehicle_returns_404(client, admin_token):
    response = client.patch("/vehicles/999/mode", json={"mode": "rent"}, headers=auth_header(admin_token))
    assert response.status_code == 404
