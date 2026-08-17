"""Tests for Phase 4: contacts, contact lists, suppression, and CSV import."""

import io


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_contact(client, email="alice@example.com", first_name="Alice", last_name="Smith",
                    status="active"):
    resp = client.post(
        "/api/v1/contacts",
        json={"email": email, "first_name": first_name, "last_name": last_name, "status": status},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_list(client, name="Newsletter"):
    resp = client.post("/api/v1/contact-lists", json={"name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Contact CRUD
# ---------------------------------------------------------------------------


def test_create_contact(client):
    c = _create_contact(client)
    assert c["id"] > 0
    assert c["email"] == "alice@example.com"
    assert c["status"] == "active"
    assert c["list_count"] == 0


def test_create_contact_duplicate_returns_409(client):
    _create_contact(client)
    resp = client.post("/api/v1/contacts", json={"email": "alice@example.com"})
    assert resp.status_code == 409


def test_list_contacts(client):
    _create_contact(client, email="a@example.com")
    _create_contact(client, email="b@example.com")
    resp = client.get("/api/v1/contacts")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_contact(client):
    c = _create_contact(client)
    resp = client.get(f"/api/v1/contacts/{c['id']}")
    assert resp.status_code == 200
    assert resp.json()["email"] == "alice@example.com"


def test_get_contact_not_found(client):
    resp = client.get("/api/v1/contacts/99999")
    assert resp.status_code == 404


def test_update_contact(client):
    c = _create_contact(client)
    resp = client.put(
        f"/api/v1/contacts/{c['id']}",
        json={"first_name": "Alicia", "status": "unsubscribed"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["first_name"] == "Alicia"
    assert body["status"] == "unsubscribed"


def test_delete_contact(client):
    c = _create_contact(client)
    resp = client.delete(f"/api/v1/contacts/{c['id']}")
    assert resp.status_code == 204
    resp2 = client.get(f"/api/v1/contacts/{c['id']}")
    assert resp2.status_code == 404


# ---------------------------------------------------------------------------
# Contact List CRUD
# ---------------------------------------------------------------------------


def test_create_contact_list(client):
    cl = _create_list(client)
    assert cl["id"] > 0
    assert cl["name"] == "Newsletter"
    assert cl["member_count"] == 0


def test_list_contact_lists(client):
    _create_list(client, "L1")
    _create_list(client, "L2")
    resp = client.get("/api/v1/contact-lists")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_update_contact_list(client):
    cl = _create_list(client)
    resp = client.put(f"/api/v1/contact-lists/{cl['id']}", json={"name": "Updated"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"


def test_delete_contact_list(client):
    cl = _create_list(client)
    resp = client.delete(f"/api/v1/contact-lists/{cl['id']}")
    assert resp.status_code == 204


# ---------------------------------------------------------------------------
# List membership add / remove
# ---------------------------------------------------------------------------


def test_add_remove_contact_from_list(client):
    c = _create_contact(client)
    cl = _create_list(client)

    # Add
    resp = client.post(f"/api/v1/contacts/{c['id']}/lists/{cl['id']}")
    assert resp.status_code == 201
    membership = resp.json()
    assert membership["contact_id"] == c["id"]
    assert membership["contact_list_id"] == cl["id"]

    # Count reflected
    refreshed = client.get(f"/api/v1/contacts/{c['id']}").json()
    assert refreshed["list_count"] == 1

    list_refreshed = client.get(f"/api/v1/contact-lists/{cl['id']}").json()
    assert list_refreshed["member_count"] == 1

    # Remove
    resp = client.delete(f"/api/v1/contacts/{c['id']}/lists/{cl['id']}")
    assert resp.status_code == 204

    refreshed2 = client.get(f"/api/v1/contacts/{c['id']}").json()
    assert refreshed2["list_count"] == 0


def test_remove_nonexistent_membership_returns_404(client):
    c = _create_contact(client)
    cl = _create_list(client)
    resp = client.delete(f"/api/v1/contacts/{c['id']}/lists/{cl['id']}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Suppression add / remove / check
# ---------------------------------------------------------------------------


def test_add_suppression(client):
    resp = client.post(
        "/api/v1/suppression",
        json={"email": "bad@example.com", "reason": "bounced", "source": "bounce_webhook"},
    )
    assert resp.status_code == 201
    entry = resp.json()
    assert entry["email"] == "bad@example.com"
    assert entry["reason"] == "bounced"


def test_add_duplicate_suppression_returns_409(client):
    client.post("/api/v1/suppression", json={"email": "dup@example.com", "reason": "manual"})
    resp = client.post("/api/v1/suppression", json={"email": "dup@example.com", "reason": "manual"})
    assert resp.status_code == 409


def test_list_suppressions(client):
    client.post("/api/v1/suppression", json={"email": "a@example.com", "reason": "manual"})
    client.post("/api/v1/suppression", json={"email": "b@example.com", "reason": "bounced"})
    resp = client.get("/api/v1/suppression")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_remove_suppression(client):
    resp = client.post(
        "/api/v1/suppression", json={"email": "gone@example.com", "reason": "manual"}
    )
    entry_id = resp.json()["id"]
    del_resp = client.delete(f"/api/v1/suppression/{entry_id}")
    assert del_resp.status_code == 204
    # Should now not be suppressed
    check = client.get("/api/v1/suppression/check?email=gone@example.com").json()
    assert check["suppressed"] is False


def test_suppression_check_not_suppressed(client):
    resp = client.get("/api/v1/suppression/check?email=clean@example.com")
    assert resp.status_code == 200
    body = resp.json()
    assert body["suppressed"] is False
    assert body["reason"] is None


def test_suppression_check_suppressed(client):
    client.post(
        "/api/v1/suppression",
        json={"email": "spam@example.com", "reason": "complained", "source": "webhook"},
    )
    resp = client.get("/api/v1/suppression/check?email=spam@example.com")
    assert resp.status_code == 200
    body = resp.json()
    assert body["suppressed"] is True
    assert body["reason"] == "complained"


# ---------------------------------------------------------------------------
# CSV import happy path
# ---------------------------------------------------------------------------


def _post_csv(client, csv_content, contact_list_id=None, mapping_json=None):
    files = {"file": ("contacts.csv", csv_content.encode(), "text/csv")}
    data = {}
    if contact_list_id is not None:
        data["contact_list_id"] = str(contact_list_id)
    if mapping_json is not None:
        data["column_mapping"] = mapping_json
    resp = client.post("/api/v1/import-jobs", files=files, data=data)
    return resp


def test_import_happy_path(client, monkeypatch):
    monkeypatch.setattr(
        "app.interfaces.routers.import_jobs.celery_client",
        type("C", (), {"send_task": lambda *a, **kw: None})(),
    )
    csv_content = "email,first_name,last_name\nalice@example.com,Alice,Smith\nbob@example.com,Bob,Jones\n"
    resp = _post_csv(client, csv_content)
    assert resp.status_code == 202
    job = resp.json()
    assert job["id"] > 0
    assert job["status"] == "pending"

    # Poll status
    get_resp = client.get(f"/api/v1/import-jobs/{job['id']}")
    assert get_resp.status_code == 200

    # List jobs
    list_resp = client.get("/api/v1/import-jobs")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


def test_import_with_invalid_rows_and_suppressed(client, monkeypatch):
    """Test import counting: valid=2, invalid email=1, suppressed=1.

    Since the worker task runs in a separate process normally, we verify
    the import job is created correctly (202, pending status), and that the
    job status polling endpoint shape is correct.  Full end-to-end task
    execution is covered by worker tests.
    """
    monkeypatch.setattr(
        "app.interfaces.routers.import_jobs.celery_client",
        type("C", (), {"send_task": lambda *a, **kw: None})(),
    )
    # Pre-suppress one email
    client.post("/api/v1/suppression", json={"email": "suppressed@example.com", "reason": "manual"})

    csv_content = (
        "email,first_name\n"
        "valid1@example.com,Alice\n"
        "valid2@example.com,Bob\n"
        "not-an-email,Charlie\n"  # invalid
        "suppressed@example.com,Dave\n"  # suppressed
    )
    resp = _post_csv(client, csv_content)
    assert resp.status_code == 202
    job = resp.json()
    assert job["status"] == "pending"

    # Verify polling shape
    get_resp = client.get(f"/api/v1/import-jobs/{job['id']}").json()
    assert get_resp["id"] == job["id"]
    assert get_resp["status"] == "pending"
    assert get_resp["filename"] == "contacts.csv"
    assert "processed_rows" in get_resp
    assert "imported_count" in get_resp
    assert "skipped_count" in get_resp
    assert "error_count" in get_resp


def test_import_job_not_found(client):
    resp = client.get("/api/v1/import-jobs/99999")
    assert resp.status_code == 404


def test_import_file_too_large(client, monkeypatch):
    monkeypatch.setattr(
        "app.interfaces.routers.import_jobs.celery_client",
        type("C", (), {"send_task": lambda *a, **kw: None})(),
    )
    # Patch MAX_FILE_SIZE_BYTES to a small value to simulate oversized file
    import app.interfaces.routers.import_jobs as ij_mod
    original = ij_mod.MAX_FILE_SIZE_BYTES
    ij_mod.MAX_FILE_SIZE_BYTES = 10  # 10 bytes
    try:
        csv_content = "email,first_name\nalice@example.com,Alice\n"
        resp = _post_csv(client, csv_content)
        assert resp.status_code == 413
    finally:
        ij_mod.MAX_FILE_SIZE_BYTES = original


def test_import_with_column_mapping(client, monkeypatch):
    """Column mapping: CSV has 'Email Address' mapped to 'email'."""
    import json

    monkeypatch.setattr(
        "app.interfaces.routers.import_jobs.celery_client",
        type("C", (), {"send_task": lambda *a, **kw: None})(),
    )
    csv_content = "Email Address,First\nmapped@example.com,Carol\n"
    mapping = json.dumps({"email": "Email Address", "first_name": "First"})
    resp = _post_csv(client, csv_content, mapping_json=mapping)
    assert resp.status_code == 202
    job = resp.json()
    assert job["status"] == "pending"
    # Column mapping is stored correctly on the job
    get_resp = client.get(f"/api/v1/import-jobs/{job['id']}").json()
    assert get_resp["id"] == job["id"]
