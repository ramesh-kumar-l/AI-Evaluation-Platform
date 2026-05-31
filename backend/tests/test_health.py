"""Phase 0 exit check: the app boots offline and reports health/readiness."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_ok(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["offline_first"] is True
    assert body["env"] == "test"


def test_ready_reaches_database(client: TestClient) -> None:
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready", "database": "ok"}
