"""Phase 1 exit check: versioned create/read with lineage for core entities, via the API."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_provider_create_and_revise_tracks_versions_and_lineage(client: TestClient) -> None:
    created = client.post("/providers", json={"name": "Local Ollama", "kind": "ollama"})
    assert created.status_code == 201
    v1 = created.json()
    assert v1["version"] == 1
    assert v1["parent_id"] is None
    assert v1["is_latest"] is True
    key = v1["entity_key"]

    revised = client.post(
        f"/providers/{key}/versions",
        json={"name": "Local Ollama", "kind": "ollama", "base_url": "http://localhost:11434"},
    )
    assert revised.status_code == 201
    v2 = revised.json()
    assert v2["version"] == 2
    assert v2["entity_key"] == key
    assert v2["parent_id"] == v1["id"]  # lineage points at the predecessor
    assert v2["is_latest"] is True

    # Latest read returns v2; full history returns both, oldest first.
    assert client.get(f"/providers/{key}").json()["version"] == 2
    history = client.get(f"/providers/{key}/versions").json()
    assert [h["version"] for h in history] == [1, 2]
    assert history[0]["is_latest"] is False


def test_dataset_derives_item_count(client: TestClient) -> None:
    resp = client.post(
        "/datasets",
        json={"name": "qa", "items": [{"input": "2+2", "expected": "4"}, {"input": "hi"}]},
    )
    assert resp.status_code == 201
    assert resp.json()["item_count"] == 2


def test_prompt_roundtrip(client: TestClient) -> None:
    resp = client.post(
        "/prompts",
        json={"name": "answer", "template": "Q: {{question}}", "input_variables": ["question"]},
    )
    assert resp.status_code == 201
    assert resp.json()["input_variables"] == ["question"]


def test_revise_unknown_entity_is_404(client: TestClient) -> None:
    missing = "00000000-0000-0000-0000-000000000000"
    resp = client.post(f"/prompts/{missing}/versions", json={"name": "x", "template": "y"})
    assert resp.status_code == 404
