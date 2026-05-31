"""Integration tests for Phase 7: Dataset & Benchmark Governance."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_benchmark(client: TestClient, name: str = "Bench-A", **kwargs: object) -> dict:
    r = client.post(
        "/benchmarks",
        json={"name": name, "domain": "nlp", "task_type": "qa", **kwargs},  # type: ignore[arg-type]
    )
    assert r.status_code == 201, r.text
    return r.json()


def _make_dataset(client: TestClient, name: str = "DS-A") -> dict:
    r = client.post(
        "/datasets",
        json={"name": name, "description": "", "items": [{"input": "q", "expected": "a"}]},
    )
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------------------
# Benchmark CRUD
# ---------------------------------------------------------------------------


def test_benchmark_create(client: TestClient) -> None:
    data = _make_benchmark(client, name="MMLU")
    assert data["name"] == "MMLU"
    assert data["status"] == "draft"
    assert data["version"] == 1
    assert data["domain"] == "nlp"
    assert data["task_type"] == "qa"
    assert isinstance(data["entity_key"], str)


def test_benchmark_list(client: TestClient) -> None:
    _make_benchmark(client, name="B1")
    _make_benchmark(client, name="B2")
    r = client.get("/benchmarks")
    assert r.status_code == 200
    names = [b["name"] for b in r.json()]
    assert "B1" in names
    assert "B2" in names


def test_benchmark_list_filter_by_status(client: TestClient) -> None:
    bench = _make_benchmark(client, name="FilterMe")
    # activate it
    client.patch(f"/benchmarks/{bench['entity_key']}/status", json={"status": "active"})
    r = client.get("/benchmarks?by_status=active")
    assert r.status_code == 200
    names = [b["name"] for b in r.json()]
    assert "FilterMe" in names

    r2 = client.get("/benchmarks?by_status=archived")
    assert r2.status_code == 200
    # freshly archived benchmarks wouldn't include FilterMe
    for b in r2.json():
        assert b["status"] == "archived"


def test_benchmark_get_not_found(client: TestClient) -> None:
    r = client.get(f"/benchmarks/{uuid.uuid4()}")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Benchmark lifecycle transitions
# ---------------------------------------------------------------------------


def test_benchmark_status_draft_to_active(client: TestClient) -> None:
    bench = _make_benchmark(client)
    r = client.patch(f"/benchmarks/{bench['entity_key']}/status", json={"status": "active"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "active"
    assert data["version"] == 2
    assert data["parent_id"] == bench["id"]


def test_benchmark_status_active_to_deprecated(client: TestClient) -> None:
    bench = _make_benchmark(client)
    client.patch(f"/benchmarks/{bench['entity_key']}/status", json={"status": "active"})
    r = client.patch(f"/benchmarks/{bench['entity_key']}/status", json={"status": "deprecated"})
    assert r.status_code == 200
    assert r.json()["status"] == "deprecated"


def test_benchmark_status_deprecated_to_archived(client: TestClient) -> None:
    bench = _make_benchmark(client)
    client.patch(f"/benchmarks/{bench['entity_key']}/status", json={"status": "active"})
    client.patch(f"/benchmarks/{bench['entity_key']}/status", json={"status": "deprecated"})
    r = client.patch(f"/benchmarks/{bench['entity_key']}/status", json={"status": "archived"})
    assert r.status_code == 200
    assert r.json()["status"] == "archived"


def test_benchmark_draft_to_deprecated_skip_active(client: TestClient) -> None:
    bench = _make_benchmark(client)
    r = client.patch(f"/benchmarks/{bench['entity_key']}/status", json={"status": "deprecated"})
    assert r.status_code == 200
    assert r.json()["status"] == "deprecated"


def test_benchmark_status_invalid_transition_422(client: TestClient) -> None:
    bench = _make_benchmark(client)
    # draft → archived is forbidden
    r = client.patch(f"/benchmarks/{bench['entity_key']}/status", json={"status": "archived"})
    assert r.status_code == 422
    assert "archived" in r.json()["detail"]


def test_benchmark_status_unknown_422(client: TestClient) -> None:
    bench = _make_benchmark(client)
    r = client.patch(f"/benchmarks/{bench['entity_key']}/status", json={"status": "nonexistent"})
    assert r.status_code == 422


def test_benchmark_transition_creates_new_version(client: TestClient) -> None:
    bench = _make_benchmark(client)
    r = client.patch(
        f"/benchmarks/{bench['entity_key']}/status",
        json={"status": "active", "notes": "ready for use"},
    )
    assert r.json()["version"] == 2
    assert r.json()["notes"] == "ready for use"
    # GET should return the latest (v2)
    r2 = client.get(f"/benchmarks/{bench['entity_key']}")
    assert r2.json()["status"] == "active"
    assert r2.json()["version"] == 2


# ---------------------------------------------------------------------------
# Dataset Policy
# ---------------------------------------------------------------------------


def test_dataset_policy_upsert_create(client: TestClient) -> None:
    ds = _make_dataset(client)
    key = ds["entity_key"]
    r = client.put(
        f"/datasets/{key}/policy",
        json={
            "owner": "ml-team",
            "status": "active",
            "quality_rules": {"min_items": 10},
            "ground_truth_policy": {"requires_review": True},
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["dataset_key"] == key
    assert data["owner"] == "ml-team"
    assert data["quality_rules"] == {"min_items": 10}
    assert data["status"] == "active"


def test_dataset_policy_upsert_update(client: TestClient) -> None:
    ds = _make_dataset(client)
    key = ds["entity_key"]
    client.put(f"/datasets/{key}/policy", json={"owner": "team-a"})
    r = client.put(f"/datasets/{key}/policy", json={"owner": "team-b", "status": "deprecated"})
    assert r.status_code == 200
    data = r.json()
    assert data["owner"] == "team-b"
    assert data["status"] == "deprecated"


def test_dataset_policy_get(client: TestClient) -> None:
    ds = _make_dataset(client)
    key = ds["entity_key"]
    client.put(f"/datasets/{key}/policy", json={"owner": "data-team"})
    r = client.get(f"/datasets/{key}/policy")
    assert r.status_code == 200
    assert r.json()["owner"] == "data-team"


def test_dataset_policy_get_not_found_404(client: TestClient) -> None:
    ds = _make_dataset(client)
    key = ds["entity_key"]
    r = client.get(f"/datasets/{key}/policy")
    assert r.status_code == 404


def test_dataset_policy_dataset_not_found_422(client: TestClient) -> None:
    r = client.put(
        f"/datasets/{uuid.uuid4()}/policy",
        json={"owner": "nobody"},
    )
    assert r.status_code == 422


def test_dataset_policy_invalid_status_422(client: TestClient) -> None:
    ds = _make_dataset(client)
    key = ds["entity_key"]
    r = client.put(f"/datasets/{key}/policy", json={"owner": "x", "status": "bogus"})
    assert r.status_code == 422
