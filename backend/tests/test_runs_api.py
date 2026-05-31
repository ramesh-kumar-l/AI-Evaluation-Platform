"""Integration tests for Phase 2: provider abstraction and inference run execution."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import httpx
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_provider(client: TestClient, base_url: str = "http://localhost:11434") -> dict:
    r = client.post(
        "/providers",
        json={
            "name": "test-ollama",
            "kind": "ollama",
            "base_url": base_url,
            "enabled": True,
            "config": {},
        },
    )
    assert r.status_code == 201
    return r.json()


def _make_model(client: TestClient, provider_key: str) -> dict:
    r = client.post(
        "/providers/models",
        json={"provider_key": provider_key, "name": "llama3", "parameters": {}},
    )
    assert r.status_code == 201
    return r.json()


def _make_prompt(client: TestClient) -> dict:
    r = client.post(
        "/prompts",
        json={
            "name": "greeting",
            "description": "",
            "template": "Hello {name}!",
            "input_variables": ["name"],
        },
    )
    assert r.status_code == 201
    return r.json()


def _mock_ollama_response(text: str = "Hi there!") -> dict:
    return {"model": "llama3", "created_at": "2024-01-01T00:00:00Z", "response": text, "done": True}


def _mock_client(text: str = "Hi there!") -> MagicMock:
    """Return a patched httpx.Client mock that returns a successful Ollama response."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = _mock_ollama_response(text)
    mock_resp.raise_for_status = MagicMock()
    mock = MagicMock()
    mock.return_value.__enter__.return_value.post.return_value = mock_resp
    return mock


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_run_success_completed(client: TestClient) -> None:
    provider = _make_provider(client)
    model = _make_model(client, provider["entity_key"])
    prompt = _make_prompt(client)

    with patch("app.services.providers.ollama.httpx.Client", _mock_client("Hi there!")):
        r = client.post(
            "/runs",
            json={
                "prompt_key": prompt["entity_key"],
                "model_key": model["entity_key"],
                "input_variables": {"name": "Alice"},
                "parameters": {"temperature": 0.0, "seed": 42},
            },
        )

    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "completed"
    assert data["raw_output"] == "Hi there!"
    assert data["rendered_prompt"] == "Hello Alice!"
    assert data["latency_ms"] >= 0
    assert data["error"] is None
    assert data["prompt_key"] == prompt["entity_key"]
    assert data["model_key"] == model["entity_key"]
    assert data["provider_key"] == provider["entity_key"]
    assert data["prompt_version_id"] == prompt["id"]
    assert data["model_version_id"] == model["id"]
    assert data["provider_version_id"] == provider["id"]


def test_run_persists_as_failed_when_provider_offline(client: TestClient) -> None:
    provider = _make_provider(client)
    model = _make_model(client, provider["entity_key"])
    prompt = _make_prompt(client)

    err_mock = MagicMock()
    err_mock.return_value.__enter__.return_value.post.side_effect = httpx.ConnectError(
        "Connection refused"
    )

    with patch("app.services.providers.ollama.httpx.Client", err_mock):
        r = client.post(
            "/runs",
            json={
                "prompt_key": prompt["entity_key"],
                "model_key": model["entity_key"],
                "input_variables": {"name": "Bob"},
                "parameters": {},
            },
        )

    # Provider failure → run persisted as failed, not a 5xx
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "failed"
    assert data["error"] is not None
    assert data["raw_output"] == ""


def test_run_missing_template_variable_is_422(client: TestClient) -> None:
    provider = _make_provider(client)
    model = _make_model(client, provider["entity_key"])
    prompt = _make_prompt(client)  # template requires "name"

    r = client.post(
        "/runs",
        json={
            "prompt_key": prompt["entity_key"],
            "model_key": model["entity_key"],
            "input_variables": {},  # "name" is missing
            "parameters": {},
        },
    )

    assert r.status_code == 422


def test_run_prompt_not_found_is_404(client: TestClient) -> None:
    provider = _make_provider(client)
    model = _make_model(client, provider["entity_key"])

    r = client.post(
        "/runs",
        json={
            "prompt_key": str(uuid.uuid4()),
            "model_key": model["entity_key"],
            "input_variables": {},
            "parameters": {},
        },
    )

    assert r.status_code == 404


def test_run_model_not_found_is_404(client: TestClient) -> None:
    prompt = _make_prompt(client)

    r = client.post(
        "/runs",
        json={
            "prompt_key": prompt["entity_key"],
            "model_key": str(uuid.uuid4()),
            "input_variables": {"name": "X"},
            "parameters": {},
        },
    )

    assert r.status_code == 404


def test_list_runs_returns_created_run(client: TestClient) -> None:
    provider = _make_provider(client)
    model = _make_model(client, provider["entity_key"])
    prompt = _make_prompt(client)

    with patch("app.services.providers.ollama.httpx.Client", _mock_client()):
        client.post(
            "/runs",
            json={
                "prompt_key": prompt["entity_key"],
                "model_key": model["entity_key"],
                "input_variables": {"name": "Carol"},
                "parameters": {},
            },
        )

    r = client.get("/runs")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_list_runs_filter_by_prompt_key(client: TestClient) -> None:
    provider = _make_provider(client)
    model = _make_model(client, provider["entity_key"])
    prompt = _make_prompt(client)

    with patch("app.services.providers.ollama.httpx.Client", _mock_client()):
        client.post(
            "/runs",
            json={
                "prompt_key": prompt["entity_key"],
                "model_key": model["entity_key"],
                "input_variables": {"name": "Dave"},
                "parameters": {},
            },
        )

    r = client.get(f"/runs?prompt_key={prompt['entity_key']}")
    assert r.status_code == 200
    assert len(r.json()) == 1

    r_no_match = client.get(f"/runs?prompt_key={uuid.uuid4()}")
    assert r_no_match.status_code == 200
    assert len(r_no_match.json()) == 0


def test_get_run_by_id(client: TestClient) -> None:
    provider = _make_provider(client)
    model = _make_model(client, provider["entity_key"])
    prompt = _make_prompt(client)

    with patch("app.services.providers.ollama.httpx.Client", _mock_client()):
        create_r = client.post(
            "/runs",
            json={
                "prompt_key": prompt["entity_key"],
                "model_key": model["entity_key"],
                "input_variables": {"name": "Eve"},
                "parameters": {},
            },
        )

    run_id = create_r.json()["id"]
    r = client.get(f"/runs/{run_id}")
    assert r.status_code == 200
    assert r.json()["id"] == run_id


def test_get_run_not_found_is_404(client: TestClient) -> None:
    r = client.get(f"/runs/{uuid.uuid4()}")
    assert r.status_code == 404


def test_run_audit_event_written(client: TestClient) -> None:
    provider = _make_provider(client)
    model = _make_model(client, provider["entity_key"])
    prompt = _make_prompt(client)

    with patch("app.services.providers.ollama.httpx.Client", _mock_client()):
        create_r = client.post(
            "/runs",
            json={
                "prompt_key": prompt["entity_key"],
                "model_key": model["entity_key"],
                "input_variables": {"name": "Frank"},
                "parameters": {},
            },
        )

    run_id = create_r.json()["id"]
    # Audit uses the run's id as entity_key
    audit_r = client.get(f"/audit/events?entity_key={run_id}")
    assert audit_r.status_code == 200
    events = audit_r.json()
    assert len(events) == 1
    assert events[0]["action"] == "run"
    assert events[0]["entity_type"] == "inference_runs"
