"""Phase 10 — Observability & Continuous Evaluation tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Shared helpers (reuse evaluation-test patterns)
# ---------------------------------------------------------------------------


def _make_provider(client: TestClient) -> dict:
    return client.post(
        "/providers",
        json={"name": "ollama", "kind": "ollama", "base_url": "http://localhost:11434",
              "enabled": True, "config": {}},
    ).json()


def _make_model(client: TestClient, provider_key: str) -> dict:
    return client.post(
        "/providers/models",
        json={"provider_key": provider_key, "name": "llama3", "parameters": {}},
    ).json()


def _make_prompt(client: TestClient) -> dict:
    return client.post(
        "/prompts",
        json={"name": "qa", "description": "", "template": "Answer: {question}",
              "input_variables": ["question"]},
    ).json()


def _make_dataset(client: TestClient) -> dict:
    return client.post(
        "/datasets",
        json={"name": "obs-ds", "description": "",
              "items": [{"input": {"question": "2+2?"}, "expected": "4"}]},
    ).json()


def _make_metric(client: TestClient) -> dict:
    return client.post(
        "/metrics",
        json={"name": "em", "description": "", "kind": "exact_match", "config": {}},
    ).json()


def _make_schedule(client: TestClient, dataset_key: str, model_key: str,
                   prompt_key: str, metric_key: str) -> dict:
    return client.post(
        "/observe/schedules",
        json={
            "name": "hourly-eval",
            "description": "Run every hour",
            "dataset_key": dataset_key,
            "model_key": model_key,
            "prompt_key": prompt_key,
            "metric_keys": [metric_key],
            "cron_expr": "0 * * * *",
        },
    ).json()


def _mock_ollama(text: str = "4") -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"model": "llama3", "response": text, "done": True}
    mock_resp.raise_for_status = MagicMock()
    mock = MagicMock()
    mock.return_value.__enter__.return_value.post.return_value = mock_resp
    return mock


# ---------------------------------------------------------------------------
# Schedule CRUD
# ---------------------------------------------------------------------------


def test_create_schedule(client: TestClient) -> None:
    prov = _make_provider(client)
    model = _make_model(client, prov["entity_key"])
    prompt = _make_prompt(client)
    ds = _make_dataset(client)
    metric = _make_metric(client)

    r = client.post(
        "/observe/schedules",
        json={
            "name": "nightly",
            "dataset_key": ds["entity_key"],
            "model_key": model["entity_key"],
            "prompt_key": prompt["entity_key"],
            "metric_keys": [metric["entity_key"]],
            "cron_expr": "0 0 * * *",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "nightly"
    assert body["status"] == "active"
    assert body["version"] == 1
    assert body["cron_expr"] == "0 0 * * *"


def test_list_schedules(client: TestClient) -> None:
    prov = _make_provider(client)
    model = _make_model(client, prov["entity_key"])
    prompt = _make_prompt(client)
    ds = _make_dataset(client)
    metric = _make_metric(client)

    _make_schedule(client, ds["entity_key"], model["entity_key"],
                   prompt["entity_key"], metric["entity_key"])

    r = client.get("/observe/schedules")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_list_schedules_filter_by_status(client: TestClient) -> None:
    prov = _make_provider(client)
    model = _make_model(client, prov["entity_key"])
    prompt = _make_prompt(client)
    ds = _make_dataset(client)
    metric = _make_metric(client)
    _make_schedule(client, ds["entity_key"], model["entity_key"],
                   prompt["entity_key"], metric["entity_key"])

    r = client.get("/observe/schedules?by_status=active")
    assert r.status_code == 200
    assert len(r.json()) == 1

    r2 = client.get("/observe/schedules?by_status=paused")
    assert r2.status_code == 200
    assert len(r2.json()) == 0


def test_get_schedule_not_found(client: TestClient) -> None:
    import uuid
    r = client.get(f"/observe/schedules/{uuid.uuid4()}")
    assert r.status_code == 404


def test_update_schedule_status_pause_and_resume(client: TestClient) -> None:
    prov = _make_provider(client)
    model = _make_model(client, prov["entity_key"])
    prompt = _make_prompt(client)
    ds = _make_dataset(client)
    metric = _make_metric(client)
    sched = _make_schedule(client, ds["entity_key"], model["entity_key"],
                           prompt["entity_key"], metric["entity_key"])

    key = sched["entity_key"]
    r = client.patch(f"/observe/schedules/{key}/status", json={"status": "paused"})
    assert r.status_code == 200
    assert r.json()["status"] == "paused"
    assert r.json()["version"] == 2

    r2 = client.patch(f"/observe/schedules/{key}/status", json={"status": "active"})
    assert r2.status_code == 200
    assert r2.json()["version"] == 3


def test_update_schedule_status_invalid(client: TestClient) -> None:
    prov = _make_provider(client)
    model = _make_model(client, prov["entity_key"])
    prompt = _make_prompt(client)
    ds = _make_dataset(client)
    metric = _make_metric(client)
    sched = _make_schedule(client, ds["entity_key"], model["entity_key"],
                           prompt["entity_key"], metric["entity_key"])

    r = client.patch(f"/observe/schedules/{sched['entity_key']}/status",
                     json={"status": "archived"})
    assert r.status_code == 422  # validator: status not in allowed set

    r2 = client.patch(f"/observe/schedules/{sched['entity_key']}/status",
                      json={"status": "bad_value"})
    assert r2.status_code == 422


# ---------------------------------------------------------------------------
# Trigger & Jobs
# ---------------------------------------------------------------------------


def test_trigger_schedule_success(client: TestClient) -> None:
    prov = _make_provider(client)
    model = _make_model(client, prov["entity_key"])
    prompt = _make_prompt(client)
    ds = _make_dataset(client)
    metric = _make_metric(client)
    sched = _make_schedule(client, ds["entity_key"], model["entity_key"],
                           prompt["entity_key"], metric["entity_key"])

    with patch("httpx.Client", _mock_ollama("4")):
        r = client.post(f"/observe/schedules/{sched['entity_key']}/trigger")

    assert r.status_code == 200
    job = r.json()
    assert job["status"] == "completed"
    assert job["eval_id"] is not None
    assert job["triggered_by"] == "manual"


def test_trigger_schedule_not_found(client: TestClient) -> None:
    import uuid
    r = client.post(f"/observe/schedules/{uuid.uuid4()}/trigger")
    assert r.status_code == 404


def test_trigger_archived_schedule_rejected(client: TestClient) -> None:
    prov = _make_provider(client)
    model = _make_model(client, prov["entity_key"])
    prompt = _make_prompt(client)
    ds = _make_dataset(client)
    metric = _make_metric(client)
    sched = _make_schedule(client, ds["entity_key"], model["entity_key"],
                           prompt["entity_key"], metric["entity_key"])
    key = sched["entity_key"]
    # pause then archive
    client.patch(f"/observe/schedules/{key}/status", json={"status": "paused"})
    client.patch(f"/observe/schedules/{key}/status", json={"status": "archived"})

    r = client.post(f"/observe/schedules/{key}/trigger")
    assert r.status_code == 422


def test_list_jobs_for_schedule(client: TestClient) -> None:
    prov = _make_provider(client)
    model = _make_model(client, prov["entity_key"])
    prompt = _make_prompt(client)
    ds = _make_dataset(client)
    metric = _make_metric(client)
    sched = _make_schedule(client, ds["entity_key"], model["entity_key"],
                           prompt["entity_key"], metric["entity_key"])

    with patch("httpx.Client", _mock_ollama("4")):
        client.post(f"/observe/schedules/{sched['entity_key']}/trigger")

    r = client.get(f"/observe/schedules/{sched['entity_key']}/jobs")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["status"] == "completed"


# ---------------------------------------------------------------------------
# Experiments
# ---------------------------------------------------------------------------


def test_create_experiment(client: TestClient) -> None:
    r = client.post(
        "/observe/experiments",
        json={"name": "model-ab", "description": "A/B test",
              "evaluation_ids": [], "hypothesis": "Model B is better"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "model-ab"
    assert body["status"] == "active"
    assert body["version"] == 1
    assert body["hypothesis"] == "Model B is better"


def test_list_experiments(client: TestClient) -> None:
    client.post("/observe/experiments",
                json={"name": "exp1", "evaluation_ids": [], "hypothesis": ""})
    client.post("/observe/experiments",
                json={"name": "exp2", "evaluation_ids": [], "hypothesis": ""})

    r = client.get("/observe/experiments")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_experiment_not_found(client: TestClient) -> None:
    import uuid
    r = client.get(f"/observe/experiments/{uuid.uuid4()}")
    assert r.status_code == 404


def test_update_experiment_adds_version(client: TestClient) -> None:
    r = client.post("/observe/experiments",
                    json={"name": "exp", "evaluation_ids": [], "hypothesis": "H1"})
    key = r.json()["entity_key"]

    import uuid
    fake_eval_id = str(uuid.uuid4())
    r2 = client.patch(
        f"/observe/experiments/{key}",
        json={"evaluation_ids": [fake_eval_id], "conclusion": "Model B wins"},
    )
    assert r2.status_code == 200
    assert r2.json()["version"] == 2
    assert r2.json()["conclusion"] == "Model B wins"
    assert len(r2.json()["evaluation_ids"]) == 1


def test_update_experiment_conclude(client: TestClient) -> None:
    r = client.post("/observe/experiments",
                    json={"name": "exp", "evaluation_ids": [], "hypothesis": ""})
    key = r.json()["entity_key"]

    r2 = client.patch(f"/observe/experiments/{key}", json={"status": "concluded"})
    assert r2.status_code == 200
    assert r2.json()["status"] == "concluded"


# ---------------------------------------------------------------------------
# Trends
# ---------------------------------------------------------------------------


def test_get_trends_empty(client: TestClient) -> None:
    import uuid
    r = client.get(f"/observe/trends?dataset_key={uuid.uuid4()}&metric_kind=exact_match")
    assert r.status_code == 200
    body = r.json()
    assert body["points"] == []
    assert body["metric_kind"] == "exact_match"


def test_get_trends_with_data(client: TestClient) -> None:
    prov = _make_provider(client)
    model = _make_model(client, prov["entity_key"])
    prompt = _make_prompt(client)
    ds = _make_dataset(client)
    metric = _make_metric(client)

    with patch("httpx.Client", _mock_ollama("4")):
        client.post(
            "/evaluations",
            json={
                "name": "trend-eval",
                "prompt_key": prompt["entity_key"],
                "model_key": model["entity_key"],
                "provider_key": prov["entity_key"],
                "dataset_key": ds["entity_key"],
                "metric_keys": [metric["entity_key"]],
                "parameters": {},
            },
        )

    r = client.get(
        f"/observe/trends?dataset_key={ds['entity_key']}&metric_kind=exact_match"
    )
    assert r.status_code == 200
    body = r.json()
    assert body["dataset_key"] == ds["entity_key"]
    assert len(body["points"]) == 1
    assert "mean_score" in body["points"][0]
