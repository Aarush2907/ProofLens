import httpx


def test_health_reports_a_live_database(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "ProofLens"
    assert body["environment"] == "test"
    assert body["database"] == "connected"
    assert body["version"] == "0.5.0"
    assert body["qdrant"] == "not_configured"
    assert "time" in body


def test_service_index_points_at_health(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["health"] == "/api/health"


def _qdrant_response(status_code: int):
    return lambda *_args, **_kwargs: httpx.Response(status_code, request=httpx.Request("GET", "http://qdrant:6333/readyz"))


def test_health_reports_a_connected_qdrant(client, monkeypatch, set_env):
    set_env(QDRANT_URL="http://qdrant:6333")
    monkeypatch.setattr(httpx, "get", _qdrant_response(200))

    body = client.get("/api/health").json()

    assert body["qdrant"] == "connected"
    assert body["status"] == "ok"


def test_health_degrades_when_qdrant_is_unreachable_or_not_ready(client, monkeypatch, set_env):
    set_env(QDRANT_URL="http://qdrant:6333")

    def refuse(*_args, **_kwargs):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(httpx, "get", refuse)
    assert client.get("/api/health").json()["qdrant"] == "unavailable"

    monkeypatch.setattr(httpx, "get", _qdrant_response(503))
    response = client.get("/api/health")
    assert response.json()["qdrant"] == "unavailable"
    assert response.json()["status"] != "ok"
