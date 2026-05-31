"""Integration tests for Phase 5: Comparison & Regression Detection."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers (subset of test_evaluations_api helpers, no cross-file import)
# ---------------------------------------------------------------------------


def _make_provider(client: TestClient) -> dict:
    r = client.post(
        "/providers",
        json={
            "name": "ollama",
            "kind": "ollama",
            "base_url": "http://localhost:11434",
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
            "name": "qa",
            "description": "",
            "template": "Answer: {question}",
            "input_variables": ["question"],
        },
    )
    assert r.status_code == 201
    return r.json()


def _make_dataset(client: TestClient) -> dict:
    items = [
        {"input": {"question": "What is 2+2?"}, "expected": "4"},
        {"input": {"question": "Capital of France?"}, "expected": "Paris"},
    ]
    r = client.post(
        "/datasets",
        json={"name": "test-ds", "description": "", "items": items, "item_count": 2},
    )
    assert r.status_code == 201
    return r.json()


def _make_metric(client: TestClient) -> dict:
    r = client.post(
        "/metrics",
        json={"name": "exact", "description": "", "kind": "exact_match", "config": {}},
    )
    assert r.status_code == 201
    return r.json()


def _mock_client(text: str = "4") -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"model": "llama3", "response": text, "done": True}
    mock_resp.raise_for_status = MagicMock()
    mock = MagicMock()
    mock.return_value.__enter__.return_value.post.return_value = mock_resp
    return mock


def _run_eval(
    client: TestClient,
    provider: dict,
    model: dict,
    prompt: dict,
    dataset: dict,
    metric: dict,
    response: str,
    name: str = "eval",
) -> dict:
    with patch("app.services.providers.ollama.httpx.Client", _mock_client(response)):
        r = client.post(
            "/evaluations",
            json={
                "name": name,
                "prompt_key": prompt["entity_key"],
                "model_key": model["entity_key"],
                "dataset_key": dataset["entity_key"],
                "metric_keys": [metric["entity_key"]],
                "parameters": {},
            },
        )
    assert r.status_code == 201
    return r.json()


def _create_comparison(
    client: TestClient,
    baseline_id: str,
    candidate_id: str,
    kind: str = "generic",
    threshold_config: dict | None = None,
) -> dict:
    r = client.post(
        "/comparisons",
        json={
            "name": "test-comp",
            "baseline_id": baseline_id,
            "candidate_id": candidate_id,
            "kind": kind,
            "threshold_config": threshold_config or {},
        },
    )
    return r.json()


# ---------------------------------------------------------------------------
# Comparison outcome tests
# ---------------------------------------------------------------------------


def test_comparison_neutral(client: TestClient) -> None:
    """Two identical evaluations → status neutral, delta = 0."""
    prov = _make_provider(client)
    model = _make_model(client, prov["entity_key"])
    prompt = _make_prompt(client)
    ds = _make_dataset(client)
    metric = _make_metric(client)

    baseline = _run_eval(client, prov, model, prompt, ds, metric, "4", "baseline")
    candidate = _run_eval(client, prov, model, prompt, ds, metric, "4", "candidate")

    r = client.post(
        "/comparisons",
        json={
            "name": "neutral-comp",
            "baseline_id": baseline["id"],
            "candidate_id": candidate["id"],
            "kind": "model",
        },
    )
    assert r.status_code == 201
    comp = r.json()
    assert comp["status"] == "neutral"
    assert comp["regressions_detected"] == 0
    assert comp["improvements_detected"] == 0
    assert comp["kind"] == "model"
    metric_key = metric["entity_key"]
    assert metric_key in comp["metric_deltas"]
    assert comp["metric_deltas"][metric_key]["delta"] == 0.0


def test_comparison_regression_detected(client: TestClient) -> None:
    """Candidate scores lower than baseline → regression."""
    prov = _make_provider(client)
    model = _make_model(client, prov["entity_key"])
    prompt = _make_prompt(client)
    ds = _make_dataset(client)
    metric = _make_metric(client)

    # Baseline: returns "4" → exact_match scores 0.5 (item 0 correct, item 1 wrong)
    baseline = _run_eval(client, prov, model, prompt, ds, metric, "4", "baseline")
    # Candidate: returns completely wrong → exact_match scores 0.0
    candidate = _run_eval(client, prov, model, prompt, ds, metric, "zzz_wrong", "candidate")

    r = client.post(
        "/comparisons",
        json={
            "name": "regression-comp",
            "baseline_id": baseline["id"],
            "candidate_id": candidate["id"],
            "kind": "model",
        },
    )
    assert r.status_code == 201
    comp = r.json()
    assert comp["status"] == "regression"
    assert comp["regressions_detected"] == 1
    assert comp["improvements_detected"] == 0
    metric_key = metric["entity_key"]
    delta_info = comp["metric_deltas"][metric_key]
    assert delta_info["regression"] is True
    assert delta_info["delta"] < 0
    assert delta_info["baseline_score"] > delta_info["candidate_score"]


def test_comparison_improvement_detected(client: TestClient) -> None:
    """Candidate scores higher than baseline → improvement."""
    prov = _make_provider(client)
    model = _make_model(client, prov["entity_key"])
    prompt = _make_prompt(client)
    ds = _make_dataset(client)
    metric = _make_metric(client)

    # Baseline: completely wrong → 0.0
    baseline = _run_eval(client, prov, model, prompt, ds, metric, "zzz_wrong", "baseline")
    # Candidate: returns "4" → 0.5
    candidate = _run_eval(client, prov, model, prompt, ds, metric, "4", "candidate")

    r = client.post(
        "/comparisons",
        json={
            "name": "improvement-comp",
            "baseline_id": baseline["id"],
            "candidate_id": candidate["id"],
        },
    )
    assert r.status_code == 201
    comp = r.json()
    assert comp["status"] == "improvement"
    assert comp["regressions_detected"] == 0
    assert comp["improvements_detected"] == 1
    metric_key = metric["entity_key"]
    delta_info = comp["metric_deltas"][metric_key]
    assert delta_info["improvement"] is True
    assert delta_info["delta"] > 0


def test_comparison_custom_threshold(client: TestClient) -> None:
    """A very high threshold suppresses regression/improvement flags → neutral."""
    prov = _make_provider(client)
    model = _make_model(client, prov["entity_key"])
    prompt = _make_prompt(client)
    ds = _make_dataset(client)
    metric = _make_metric(client)

    baseline = _run_eval(client, prov, model, prompt, ds, metric, "4", "baseline")
    candidate = _run_eval(client, prov, model, prompt, ds, metric, "zzz_wrong", "candidate")

    metric_key = metric["entity_key"]
    r = client.post(
        "/comparisons",
        json={
            "name": "high-threshold-comp",
            "baseline_id": baseline["id"],
            "candidate_id": candidate["id"],
            # Threshold of 1.0 means the full range of scores won't flag anything
            "threshold_config": {metric_key: 1.0},
        },
    )
    assert r.status_code == 201
    comp = r.json()
    assert comp["status"] == "neutral"
    assert comp["regressions_detected"] == 0


def test_comparison_records_audit_event(client: TestClient) -> None:
    """Creating a comparison emits an audit event."""
    prov = _make_provider(client)
    model = _make_model(client, prov["entity_key"])
    prompt = _make_prompt(client)
    ds = _make_dataset(client)
    metric = _make_metric(client)

    baseline = _run_eval(client, prov, model, prompt, ds, metric, "4", "baseline")
    candidate = _run_eval(client, prov, model, prompt, ds, metric, "4", "candidate")

    comp_r = client.post(
        "/comparisons",
        json={"name": "audit-comp", "baseline_id": baseline["id"], "candidate_id": candidate["id"]},
    )
    assert comp_r.status_code == 201
    comp_id = comp_r.json()["id"]

    audit_r = client.get(f"/audit/events?entity_key={comp_id}")
    assert audit_r.status_code == 200
    events = audit_r.json()
    assert len(events) == 1
    assert events[0]["entity_type"] == "comparisons"
    assert events[0]["action"] == "create"


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


def test_comparison_mismatched_datasets_422(client: TestClient) -> None:
    """Evaluations on different datasets must be rejected."""
    prov = _make_provider(client)
    model = _make_model(client, prov["entity_key"])
    prompt = _make_prompt(client)
    metric = _make_metric(client)

    ds1_r = client.post(
        "/datasets",
        json={
            "name": "ds1",
            "description": "",
            "items": [{"input": {}, "expected": "a"}],
            "item_count": 1,
        },
    )
    ds2_r = client.post(
        "/datasets",
        json={
            "name": "ds2",
            "description": "",
            "items": [{"input": {}, "expected": "b"}],
            "item_count": 1,
        },
    )
    ds1 = ds1_r.json()
    ds2 = ds2_r.json()

    with patch("app.services.providers.ollama.httpx.Client", _mock_client("a")):
        ev1 = client.post(
            "/evaluations",
            json={
                "name": "e1",
                "prompt_key": prompt["entity_key"],
                "model_key": model["entity_key"],
                "dataset_key": ds1["entity_key"],
                "metric_keys": [metric["entity_key"]],
                "parameters": {},
            },
        ).json()

    with patch("app.services.providers.ollama.httpx.Client", _mock_client("b")):
        ev2 = client.post(
            "/evaluations",
            json={
                "name": "e2",
                "prompt_key": prompt["entity_key"],
                "model_key": model["entity_key"],
                "dataset_key": ds2["entity_key"],
                "metric_keys": [metric["entity_key"]],
                "parameters": {},
            },
        ).json()

    r = client.post(
        "/comparisons",
        json={"name": "bad-comp", "baseline_id": ev1["id"], "candidate_id": ev2["id"]},
    )
    assert r.status_code == 422
    assert "dataset_key" in r.json()["detail"]


def test_comparison_baseline_not_found_404(client: TestClient) -> None:
    prov = _make_provider(client)
    model = _make_model(client, prov["entity_key"])
    prompt = _make_prompt(client)
    ds = _make_dataset(client)
    metric = _make_metric(client)

    candidate = _run_eval(client, prov, model, prompt, ds, metric, "4", "candidate")

    r = client.post(
        "/comparisons",
        json={"name": "bad", "baseline_id": str(uuid.uuid4()), "candidate_id": candidate["id"]},
    )
    assert r.status_code == 404


def test_comparison_candidate_not_found_404(client: TestClient) -> None:
    prov = _make_provider(client)
    model = _make_model(client, prov["entity_key"])
    prompt = _make_prompt(client)
    ds = _make_dataset(client)
    metric = _make_metric(client)

    baseline = _run_eval(client, prov, model, prompt, ds, metric, "4", "baseline")

    r = client.post(
        "/comparisons",
        json={"name": "bad", "baseline_id": baseline["id"], "candidate_id": str(uuid.uuid4())},
    )
    assert r.status_code == 404


def test_comparison_invalid_kind_422(client: TestClient) -> None:
    r = client.post(
        "/comparisons",
        json={
            "name": "x",
            "baseline_id": str(uuid.uuid4()),
            "candidate_id": str(uuid.uuid4()),
            "kind": "invalid_kind",
        },
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# List / get
# ---------------------------------------------------------------------------


def test_comparison_list_and_get(client: TestClient) -> None:
    prov = _make_provider(client)
    model = _make_model(client, prov["entity_key"])
    prompt = _make_prompt(client)
    ds = _make_dataset(client)
    metric = _make_metric(client)

    baseline = _run_eval(client, prov, model, prompt, ds, metric, "4", "baseline")
    candidate = _run_eval(client, prov, model, prompt, ds, metric, "4", "candidate")

    comp = _create_comparison(client, baseline["id"], candidate["id"])
    comp_id = comp["id"]

    list_r = client.get("/comparisons")
    assert list_r.status_code == 200
    assert len(list_r.json()) == 1

    get_r = client.get(f"/comparisons/{comp_id}")
    assert get_r.status_code == 200
    assert get_r.json()["id"] == comp_id


def test_comparison_list_filter_by_status(client: TestClient) -> None:
    prov = _make_provider(client)
    model = _make_model(client, prov["entity_key"])
    prompt = _make_prompt(client)
    ds = _make_dataset(client)
    metric = _make_metric(client)

    baseline = _run_eval(client, prov, model, prompt, ds, metric, "4", "b")
    candidate_same = _run_eval(client, prov, model, prompt, ds, metric, "4", "c1")
    candidate_bad = _run_eval(client, prov, model, prompt, ds, metric, "zzz", "c2")

    _create_comparison(client, baseline["id"], candidate_same["id"])  # neutral
    _create_comparison(client, baseline["id"], candidate_bad["id"])  # regression

    neutral = client.get("/comparisons?status=neutral").json()
    regression = client.get("/comparisons?status=regression").json()
    assert len(neutral) == 1
    assert len(regression) == 1


def test_comparison_get_not_found_404(client: TestClient) -> None:
    r = client.get(f"/comparisons/{uuid.uuid4()}")
    assert r.status_code == 404
