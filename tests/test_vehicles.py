def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def vehicle_payload(**overrides):
    payload = {
        "brand": "Renault",
        "model": "Clio",
        "year": 2022,
        "mileage": 10000,
        "color": "Bleu",
        "fuel_type": "essence",
        "price_sale": 9000,
        "mode": "sale",
    }
    payload.update(overrides)
    return payload


def test_create_vehicle_requires_admin(client, client_token):
    response = client.post("/vehicles", json=vehicle_payload(), headers=auth_header(client_token))
    assert response.status_code == 403


def test_admin_can_create_vehicle_for_sale(client, admin_token):
    response = client.post("/vehicles", json=vehicle_payload(), headers=auth_header(admin_token))
    assert response.status_code == 201
    assert response.json()["mode"] == "sale"
    assert response.json()["year"] == 2022
    assert response.json()["fuel_type"] == "essence"


def test_create_vehicle_for_rent_requires_monthly_price(client, admin_token):
    response = client.post(
        "/vehicles",
        json=vehicle_payload(brand="Peugeot", model="208", mode="rent", price_sale=None),
        headers=auth_header(admin_token),
    )
    assert response.status_code == 422


def test_list_vehicles_filters_by_mode(client, admin_token):
    client.post("/vehicles", json=vehicle_payload(), headers=auth_header(admin_token))
    client.post(
        "/vehicles",
        json=vehicle_payload(
            brand="Peugeot", model="208", price_sale=None, price_rent_monthly=250, mode="rent"
        ),
        headers=auth_header(admin_token),
    )
    response = client.get("/vehicles", params={"mode": "rent"})
    assert response.status_code == 200
    brands = [v["brand"] for v in response.json()]
    assert brands == ["Peugeot"]


def test_get_vehicle_detail(client, admin_token):
    create = client.post("/vehicles", json=vehicle_payload(description="Petite citadine."), headers=auth_header(admin_token))
    vehicle_id = create.json()["id"]
    response = client.get(f"/vehicles/{vehicle_id}")
    assert response.status_code == 200
    assert response.json()["description"] == "Petite citadine."


def test_get_unknown_vehicle_detail_returns_404(client):
    response = client.get("/vehicles/999")
    assert response.status_code == 404


def test_toggle_vehicle_mode(client, admin_token):
    create = client.post(
        "/vehicles",
        json=vehicle_payload(brand="Citroen", model="C3", price_rent_monthly=200),
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
