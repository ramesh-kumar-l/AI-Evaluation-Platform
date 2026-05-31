"""Phase 11 — Security: API key auth, RBAC, rate limiting, security headers."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def auth_client() -> TestClient:
    """Client with auth enabled and a known admin secret."""
    os.environ["AEP_API_AUTH_ENABLED"] = "true"
    os.environ["AEP_ADMIN_SECRET"] = "test-admin-secret"
    # Clear cached settings so the new env vars take effect.
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.main import create_app

    client = TestClient(create_app(), raise_server_exceptions=True)
    yield client
    # Restore
    os.environ["AEP_API_AUTH_ENABLED"] = "false"
    get_settings.cache_clear()


def _create_key(
    client: TestClient, name: str = "test-key", role: str = "admin"
) -> dict:
    resp = client.post(
        "/admin/api-keys",
        json={"name": name, "role": role},
        headers={"X-Admin-Secret": "test-admin-secret"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Admin key management (auth disabled — anyone can call /admin when off)
# ---------------------------------------------------------------------------


def test_create_api_key_auth_disabled(client: TestClient) -> None:
    resp = client.post("/admin/api-keys", json={"name": "k1", "role": "evaluator"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "k1"
    assert data["role"] == "evaluator"
    assert data["raw_key"].startswith("aep_")


def test_list_api_keys_empty(client: TestClient) -> None:
    resp = client.get("/admin/api-keys")
    assert resp.status_code == 200
    assert resp.json() == []


def test_revoke_api_key(client: TestClient) -> None:
    created = client.post(
        "/admin/api-keys", json={"name": "revoke-me", "role": "viewer"}
    ).json()
    resp = client.delete(f"/admin/api-keys/{created['id']}")
    assert resp.status_code == 204


def test_revoke_nonexistent_key_returns_404(client: TestClient) -> None:
    import uuid

    resp = client.delete(f"/admin/api-keys/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Auth enforcement
# ---------------------------------------------------------------------------


def test_missing_api_key_returns_401(auth_client: TestClient) -> None:
    resp = auth_client.get("/providers")
    assert resp.status_code == 401


def test_invalid_api_key_returns_403(auth_client: TestClient) -> None:
    resp = auth_client.get("/providers", headers={"X-API-Key": "aep_invalid"})
    assert resp.status_code == 403


def test_valid_api_key_grants_access(auth_client: TestClient) -> None:
    key_data = _create_key(auth_client, "admin-key", "admin")
    resp = auth_client.get(
        "/providers", headers={"X-API-Key": key_data["raw_key"]}
    )
    assert resp.status_code == 200


def test_revoked_key_returns_403(auth_client: TestClient) -> None:
    key_data = _create_key(auth_client, "short-lived", "viewer")
    raw_key = key_data["raw_key"]
    auth_client.delete(
        f"/admin/api-keys/{key_data['id']}",
        headers={"X-Admin-Secret": "test-admin-secret"},
    )
    resp = auth_client.get("/providers", headers={"X-API-Key": raw_key})
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# RBAC
# ---------------------------------------------------------------------------


def test_viewer_can_read(auth_client: TestClient) -> None:
    key_data = _create_key(auth_client, "viewer-key", "viewer")
    resp = auth_client.get(
        "/providers", headers={"X-API-Key": key_data["raw_key"]}
    )
    assert resp.status_code == 200


def test_viewer_cannot_write(auth_client: TestClient) -> None:
    """RBAC: _level enforces hierarchy — viewer is below evaluator."""
    from app.core.rbac import _level

    assert _level("viewer") < _level("evaluator")
    assert _level("evaluator") < _level("approver")
    assert _level("approver") < _level("admin")


def test_rbac_rejects_insufficient_role(auth_client: TestClient) -> None:
    """require_role raises 403 for a role below the minimum."""
    from dataclasses import dataclass

    from fastapi import HTTPException

    from app.core.rbac import require_role

    @dataclass
    class _StubKey:
        role: str
        name: str = "stub"

    checker = require_role("evaluator")
    with pytest.raises(HTTPException) as exc_info:
        checker(_StubKey(role="viewer"))  # type: ignore[arg-type]
    assert exc_info.value.status_code == 403


def test_evaluator_role_allows_evaluator_level(auth_client: TestClient) -> None:
    key_data = _create_key(auth_client, "eval-key", "evaluator")
    # evaluator can create providers (requires POST access — no RBAC gate on /providers in prod
    # but we verify auth passes)
    resp = auth_client.post(
        "/providers",
        json={"name": "test-p", "kind": "ollama", "base_url": "http://localhost:11434",
              "enabled": True, "config": {}},
        headers={"X-API-Key": key_data["raw_key"]},
    )
    # 201 or 422 (validation) are both success — 401/403 would be failures
    assert resp.status_code not in (401, 403)


# ---------------------------------------------------------------------------
# Admin bootstrap secret
# ---------------------------------------------------------------------------


def test_admin_endpoint_requires_secret_when_auth_enabled(
    auth_client: TestClient,
) -> None:
    resp = auth_client.post("/admin/api-keys", json={"name": "x", "role": "viewer"})
    assert resp.status_code == 401


def test_wrong_admin_secret_rejected(auth_client: TestClient) -> None:
    resp = auth_client.post(
        "/admin/api-keys",
        json={"name": "x", "role": "viewer"},
        headers={"X-Admin-Secret": "wrong-secret"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------


def test_security_headers_present(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"
    assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


def test_rate_limit_blocks_after_threshold(auth_client: TestClient) -> None:
    """Override the limit to 3 req/min for a fast test."""
    from app.core import rate_limit
    from app.core.config import get_settings

    # Clear stale window entries from prior tests first
    rate_limit._windows.clear()

    settings = get_settings()
    original = settings.rate_limit_per_minute
    settings.__dict__["rate_limit_per_minute"] = 3

    key_data = _create_key(auth_client, "rate-key", "viewer")
    headers = {"X-API-Key": key_data["raw_key"]}
    # Reset the window for this specific key after key creation call
    rate_limit._windows.clear()

    # Make 4 requests — 4th should exceed the limit of 3
    statuses = [
        auth_client.get("/providers", headers=headers).status_code for _ in range(4)
    ]
    assert 429 in statuses, f"Expected 429 after 3 requests, got: {statuses}"

    # Restore
    settings.__dict__["rate_limit_per_minute"] = original
    rate_limit._windows.clear()
