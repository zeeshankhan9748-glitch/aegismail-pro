def create_provider(client, name="Primary SMTP"):
    response = client.post(
        "/api/v1/smtp-providers",
        json={
            "name": name,
            "host": "smtp.example.com",
            "port": 587,
            "username": "mailer",
            "password": "top-secret",
            "use_tls": True,
            "use_ssl": False,
            "throttle_limit_per_minute": 60,
        },
    )
    return response.json()


def create_sender_identity(client, provider_id: int):
    response = client.post(
        "/api/v1/sender-identities",
        json={
            "smtp_provider_id": provider_id,
            "display_name": "Demo Sender",
            "from_email": "noreply@example.com",
            "reply_to_email": "support@example.com",
        },
    )
    return response.json()


def test_send_message_creates_queued_record_and_enqueues_task(client, monkeypatch):
    provider = create_provider(client)
    sender_identity = create_sender_identity(client, provider["id"])
    queued = []

    monkeypatch.setattr(
        "app.interfaces.routers.messages.enqueue_send_email",
        lambda message_id: queued.append(message_id),
    )

    response = client.post(
        "/api/v1/messages/send",
        json={
            "provider_id": provider["id"],
            "sender_identity_id": sender_identity["id"],
            "recipient_email": "hello@example.com",
            "subject": "Test message",
            "body_text": "Plain body",
            "body_html": "<p>HTML body</p>",
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert queued == [body["id"]]

    list_response = client.get("/api/v1/messages")
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1
    assert list_response.json()["items"][0]["recipient_email"] == "hello@example.com"


def test_send_message_deduplicates_by_idempotency_key(client, monkeypatch):
    provider = create_provider(client)
    sender_identity = create_sender_identity(client, provider["id"])
    queued = []

    monkeypatch.setattr(
        "app.interfaces.routers.messages.enqueue_send_email",
        lambda message_id: queued.append(message_id),
    )

    payload = {
        "provider_id": provider["id"],
        "sender_identity_id": sender_identity["id"],
        "recipient_email": "hello@example.com",
        "subject": "Test message",
        "body_text": "Plain body",
    }

    first = client.post(
        "/api/v1/messages/send",
        json=payload,
        headers={"Idempotency-Key": "message-123"},
    )
    second = client.post(
        "/api/v1/messages/send",
        json=payload,
        headers={"Idempotency-Key": "message-123"},
    )

    assert first.status_code == 202
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert queued == [first.json()["id"]]


def test_send_message_rejects_sender_identity_from_other_provider(client):
    provider = create_provider(client, name="Primary SMTP")
    other_provider = create_provider(client, name="Backup SMTP")
    sender_identity = create_sender_identity(client, other_provider["id"])

    response = client.post(
        "/api/v1/messages/send",
        json={
            "provider_id": provider["id"],
            "sender_identity_id": sender_identity["id"],
            "recipient_email": "hello@example.com",
            "subject": "Test message",
            "body_text": "Plain body",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Sender identity does not belong to the selected SMTP provider"
