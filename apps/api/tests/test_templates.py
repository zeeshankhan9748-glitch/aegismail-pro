"""Tests for Phase 3 template builder, preview, and placeholder validation."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_template(client, name="Welcome Email", subject="Hello {{first_name}}",
                     body_text="Hi {{first_name}}, welcome!", body_html=None, description=None):
    payload = {
        "name": name,
        "subject_template": subject,
        "body_text_template": body_text,
    }
    if body_html is not None:
        payload["body_html_template"] = body_html
    if description is not None:
        payload["description"] = description
    resp = client.post("/api/v1/templates", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_provider(client):
    resp = client.post(
        "/api/v1/smtp-providers",
        json={
            "name": "TestSMTP",
            "host": "smtp.example.com",
            "port": 587,
            "use_tls": True,
            "use_ssl": False,
            "throttle_limit_per_minute": 60,
        },
    )
    return resp.json()


def _create_identity(client, provider_id):
    resp = client.post(
        "/api/v1/sender-identities",
        json={
            "smtp_provider_id": provider_id,
            "display_name": "Sender",
            "from_email": "noreply@example.com",
        },
    )
    return resp.json()


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def test_create_template(client):
    tmpl = _create_template(client)
    assert tmpl["id"] > 0
    assert tmpl["name"] == "Welcome Email"
    assert tmpl["current_version_id"] is not None
    assert tmpl["current_version"]["version_number"] == 1


def test_list_templates(client):
    _create_template(client, name="T1")
    _create_template(client, name="T2")
    resp = client.get("/api/v1/templates")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_template(client):
    tmpl = _create_template(client)
    resp = client.get(f"/api/v1/templates/{tmpl['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == tmpl["id"]


def test_update_template_metadata(client):
    tmpl = _create_template(client, description="old desc")
    resp = client.put(
        f"/api/v1/templates/{tmpl['id']}",
        json={"name": "New Name", "description": "new desc"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "New Name"
    assert body["description"] == "new desc"


def test_get_template_not_found(client):
    resp = client.get("/api/v1/templates/99999")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------

def test_create_new_version(client):
    tmpl = _create_template(client)
    resp = client.post(
        f"/api/v1/templates/{tmpl['id']}/versions",
        json={
            "subject_template": "Hello {{last_name}}",
            "body_text_template": "Hi {{last_name}}",
        },
    )
    assert resp.status_code == 201
    ver = resp.json()
    assert ver["version_number"] == 2

    # current version should now be v2
    updated = client.get(f"/api/v1/templates/{tmpl['id']}").json()
    assert updated["current_version_id"] == ver["id"]


def test_list_versions(client):
    tmpl = _create_template(client)
    client.post(
        f"/api/v1/templates/{tmpl['id']}/versions",
        json={"subject_template": "S2", "body_text_template": "B2"},
    )
    resp = client.get(f"/api/v1/templates/{tmpl['id']}/versions")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_rollback_version(client):
    tmpl = _create_template(client)
    v1_id = tmpl["current_version_id"]
    # create v2
    v2 = client.post(
        f"/api/v1/templates/{tmpl['id']}/versions",
        json={"subject_template": "S2", "body_text_template": "B2"},
    ).json()
    assert v2["version_number"] == 2

    # rollback to v1
    resp = client.post(f"/api/v1/templates/{tmpl['id']}/versions/{v1_id}/rollback")
    assert resp.status_code == 200
    assert resp.json()["current_version_id"] == v1_id


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------

def test_preview_with_all_vars(client):
    tmpl = _create_template(
        client,
        subject="Hello {{first_name}}",
        body_text="Hi {{first_name}}, welcome to {{company}}!",
    )
    resp = client.post(
        f"/api/v1/templates/{tmpl['id']}/preview",
        json={"variables": {"first_name": "Alice", "company": "Acme"}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["subject"] == "Hello Alice"
    assert "Alice" in body["body_text"]
    assert body["inspector"]["all_present"] is True
    assert body["inspector"]["missing_placeholders"] == []
    assert body["inspector"]["unknown_payload_keys"] == []


def test_preview_detects_missing_placeholders(client):
    tmpl = _create_template(client, subject="Hi {{first_name}}", body_text="Hello {{last_name}}")
    resp = client.post(
        f"/api/v1/templates/{tmpl['id']}/preview",
        json={"variables": {"first_name": "Alice"}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "last_name" in body["inspector"]["missing_placeholders"]
    assert body["inspector"]["all_present"] is False


def test_preview_detects_unknown_payload_keys(client):
    tmpl = _create_template(client, subject="Hi {{name}}", body_text="Hello {{name}}")
    resp = client.post(
        f"/api/v1/templates/{tmpl['id']}/preview",
        json={"variables": {"name": "Bob", "unused_key": "X"}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "unused_key" in body["inspector"]["unknown_payload_keys"]


def test_preview_html_safety_warning(client):
    tmpl = _create_template(
        client,
        body_html="<script>alert(1)</script>Hello",
        body_text="Hello",
        subject="Subj",
    )
    resp = client.post(f"/api/v1/templates/{tmpl['id']}/preview", json={"variables": {}})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["html_safety_warnings"]) > 0
    assert any("<script" in w for w in body["html_safety_warnings"])


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

def test_validate_all_present(client):
    tmpl = _create_template(client, subject="Hi {{name}}", body_text="Hello {{name}}")
    resp = client.post(f"/api/v1/templates/{tmpl['id']}/validate", json={"variables": {"name": "X"}})
    assert resp.status_code == 200
    body = resp.json()
    assert body["valid"] is True
    assert body["missing_placeholders"] == []


def test_validate_missing_returns_invalid(client):
    tmpl = _create_template(client, subject="Hi {{name}}", body_text="Hello {{name}}")
    resp = client.post(f"/api/v1/templates/{tmpl['id']}/validate", json={"variables": {}})
    assert resp.status_code == 200
    body = resp.json()
    assert body["valid"] is False
    assert "name" in body["missing_placeholders"]


# ---------------------------------------------------------------------------
# Extended /messages/send with template
# ---------------------------------------------------------------------------

def test_send_with_template(client, monkeypatch):
    provider = _create_provider(client)
    identity = _create_identity(client, provider["id"])
    tmpl = _create_template(
        client,
        subject="Hello {{first_name}}",
        body_text="Hi {{first_name}}",
    )

    queued = []
    monkeypatch.setattr(
        "app.interfaces.routers.messages.enqueue_send_email",
        lambda mid: queued.append(mid),
    )

    resp = client.post(
        "/api/v1/messages/send",
        json={
            "provider_id": provider["id"],
            "sender_identity_id": identity["id"],
            "recipient_email": "user@example.com",
            "template_id": tmpl["id"],
            "variables": {"first_name": "Alice"},
        },
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["subject"] == "Hello Alice"
    assert body["body_text"] == "Hi Alice"
    assert queued == [body["id"]]


def test_send_with_template_missing_vars_returns_422(client, monkeypatch):
    provider = _create_provider(client)
    identity = _create_identity(client, provider["id"])
    tmpl = _create_template(client, subject="Hi {{name}}", body_text="Hello {{name}}")

    monkeypatch.setattr(
        "app.interfaces.routers.messages.enqueue_send_email",
        lambda mid: None,
    )

    resp = client.post(
        "/api/v1/messages/send",
        json={
            "provider_id": provider["id"],
            "sender_identity_id": identity["id"],
            "recipient_email": "user@example.com",
            "template_id": tmpl["id"],
            "variables": {},
        },
    )
    assert resp.status_code == 422
    assert "name" in resp.json()["detail"]


def test_send_without_template_still_works(client, monkeypatch):
    provider = _create_provider(client)
    identity = _create_identity(client, provider["id"])

    queued = []
    monkeypatch.setattr(
        "app.interfaces.routers.messages.enqueue_send_email",
        lambda mid: queued.append(mid),
    )

    resp = client.post(
        "/api/v1/messages/send",
        json={
            "provider_id": provider["id"],
            "sender_identity_id": identity["id"],
            "recipient_email": "user@example.com",
            "subject": "Raw subject",
            "body_text": "Raw body",
        },
    )
    assert resp.status_code == 202
    assert resp.json()["subject"] == "Raw subject"
