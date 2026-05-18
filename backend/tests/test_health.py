def test_health_reports_a_live_database(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "ProofLens"
    assert body["environment"] == "test"
    assert body["database"] == "connected"
    assert body["version"] == "0.3.0"
    assert "time" in body


def test_service_index_points_at_health(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["health"] == "/api/health"
