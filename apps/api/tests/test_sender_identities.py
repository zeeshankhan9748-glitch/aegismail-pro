def test_create_list_and_get_sender_identity(client):
    provider_response = client.post(
        "/api/v1/smtp-providers",
        json={
            "name": "Primary SMTP",
            "host": "smtp.example.com",
            "port": 587,
            "username": "mailer",
            "password": "top-secret",
            "use_tls": True,
        },
    )
    provider_id = provider_response.json()["id"]

    create_response = client.post(
        "/api/v1/sender-identities",
        json={
            "smtp_provider_id": provider_id,
            "display_name": "Demo Sender",
            "from_email": "noreply@example.com",
            "reply_to_email": "support@example.com",
        },
    )

    assert create_response.status_code == 201
    body = create_response.json()
    assert body["display_name"] == "Demo Sender"

    list_response = client.get("/api/v1/sender-identities")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/api/v1/sender-identities/{body['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["from_email"] == "noreply@example.com"


def test_create_sender_identity_requires_existing_provider(client):
    response = client.post(
        "/api/v1/sender-identities",
        json={
            "smtp_provider_id": 999,
            "display_name": "Missing Provider Sender",
            "from_email": "missing@example.com",
            "reply_to_email": "support@example.com",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "SMTP provider not found"
