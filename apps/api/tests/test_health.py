def test_healthcheck(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness(client):
    response = client.get("/ready")

    assert response.status_code == 200
    assert "Database connectivity" in response.json()["detail"]
