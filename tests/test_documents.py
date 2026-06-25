import io


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def _create_dossier(client, client_token, admin_token):
    vehicle = client.post(
        "/vehicles",
        json={"brand": "Renault", "model": "Clio", "mileage": 1000, "price_sale": 9000, "mode": "sale"},
        headers=auth_header(admin_token),
    ).json()
    dossier = client.post(
        "/dossiers", json={"vehicle_id": vehicle["id"], "type": "achat"}, headers=auth_header(client_token)
    ).json()
    return dossier["id"]


def test_upload_valid_pdf_document(client, client_token, admin_token, tmp_path, monkeypatch):
    from app import config

    monkeypatch.setattr(config.settings, "upload_dir", str(tmp_path))
    dossier_id = _create_dossier(client, client_token, admin_token)

    response = client.post(
        f"/documents/{dossier_id}",
        files={"file": ("piece_identite.pdf", io.BytesIO(b"%PDF-1.4 fake content"), "application/pdf")},
        headers=auth_header(client_token),
    )
    assert response.status_code == 201
    assert response.json()["filename"] == "piece_identite.pdf"


def test_upload_rejects_unsupported_content_type(client, client_token, admin_token, tmp_path, monkeypatch):
    from app import config

    monkeypatch.setattr(config.settings, "upload_dir", str(tmp_path))
    dossier_id = _create_dossier(client, client_token, admin_token)

    response = client.post(
        f"/documents/{dossier_id}",
        files={"file": ("malware.exe", io.BytesIO(b"binary"), "application/x-msdownload")},
        headers=auth_header(client_token),
    )
    assert response.status_code == 415


def test_upload_rejects_oversized_file(client, client_token, admin_token, tmp_path, monkeypatch):
    from app import config

    monkeypatch.setattr(config.settings, "upload_dir", str(tmp_path))
    monkeypatch.setattr(config.settings, "max_upload_size_mb", 0)
    dossier_id = _create_dossier(client, client_token, admin_token)

    response = client.post(
        f"/documents/{dossier_id}",
        files={"file": ("piece.pdf", io.BytesIO(b"x" * 1024), "application/pdf")},
        headers=auth_header(client_token),
    )
    assert response.status_code == 413


def test_upload_to_unknown_dossier_returns_404(client, client_token):
    response = client.post(
        "/documents/999",
        files={"file": ("piece.pdf", io.BytesIO(b"x"), "application/pdf")},
        headers=auth_header(client_token),
    )
    assert response.status_code == 404


def test_list_documents_for_dossier(client, client_token, admin_token, tmp_path, monkeypatch):
    from app import config

    monkeypatch.setattr(config.settings, "upload_dir", str(tmp_path))
    dossier_id = _create_dossier(client, client_token, admin_token)
    client.post(
        f"/documents/{dossier_id}",
        files={"file": ("piece.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
        headers=auth_header(client_token),
    )

    response = client.get(f"/documents/{dossier_id}", headers=auth_header(client_token))
    assert response.status_code == 200
    assert len(response.json()) == 1
