def test_create_and_get_smtp_provider(client):
    payload = {
        "name": "Primary SMTP",
        "host": "smtp.example.com",
        "port": 587,
        "username": "mailer",
        "password": "top-secret",
        "use_tls": True,
    }

    create_response = client.post("/api/v1/smtp-providers", json=payload)
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["name"] == payload["name"]
    assert "password" not in body

    list_response = client.get("/api/v1/smtp-providers")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/api/v1/smtp-providers/{body['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["host"] == payload["host"]
