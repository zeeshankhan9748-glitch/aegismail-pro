import smtplib


def test_create_update_and_get_smtp_provider(client):
    payload = {
        "name": "Primary SMTP",
        "host": "smtp.example.com",
        "port": 587,
        "username": "mailer",
        "password": "top-secret",
        "use_tls": True,
        "use_ssl": False,
        "throttle_limit_per_minute": 75,
    }

    create_response = client.post("/api/v1/smtp-providers", json=payload)
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["name"] == payload["name"]
    assert "password" not in body
    assert body["use_ssl"] is False
    assert body["throttle_limit_per_minute"] == 75

    update_response = client.put(
        f"/api/v1/smtp-providers/{body['id']}",
        json={
            **payload,
            "host": "smtp.mailpit.local",
            "port": 465,
            "password": "",
            "use_tls": False,
            "use_ssl": True,
            "throttle_limit_per_minute": 120,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["use_ssl"] is True
    assert update_response.json()["throttle_limit_per_minute"] == 120

    list_response = client.get("/api/v1/smtp-providers")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/api/v1/smtp-providers/{body['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["host"] == "smtp.mailpit.local"


def test_test_connection_success(client, monkeypatch):
    provider = client.post(
        "/api/v1/smtp-providers",
        json={
            "name": "Primary SMTP",
            "host": "smtp.example.com",
            "port": 587,
            "username": "mailer",
            "password": "top-secret",
            "use_tls": True,
            "use_ssl": False,
            "throttle_limit_per_minute": 60,
        },
    ).json()

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            assert host == "smtp.example.com"
            assert port == 587
            assert timeout == 10

        def ehlo(self):
            return None

        def starttls(self):
            return None

        def login(self, username, password):
            assert username == "mailer"
            assert password == "top-secret"

        def quit(self):
            return None

    monkeypatch.setattr("app.application.services.smtp_delivery.smtplib.SMTP", FakeSMTP)

    response = client.post(f"/api/v1/smtp-providers/{provider['id']}/test-connection")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "provider_id": provider["id"],
        "message": "SMTP connection successful",
    }


def test_test_connection_failure_returns_sanitized_message(client, monkeypatch):
    provider = client.post(
        "/api/v1/smtp-providers",
        json={
            "name": "Broken SMTP",
            "host": "smtp.example.com",
            "port": 465,
            "username": "mailer",
            "password": "top-secret",
            "use_tls": False,
            "use_ssl": True,
            "throttle_limit_per_minute": 60,
        },
    ).json()

    class FakeSMTPSSL:
        def __init__(self, host, port, timeout):
            raise smtplib.SMTPAuthenticationError(535, b"invalid credentials")

    monkeypatch.setattr("app.application.services.smtp_delivery.smtplib.SMTP_SSL", FakeSMTPSSL)

    response = client.post(f"/api/v1/smtp-providers/{provider['id']}/test-connection")

    assert response.status_code == 200
    assert response.json()["success"] is False
    assert "invalid credentials" in response.json()["message"]
