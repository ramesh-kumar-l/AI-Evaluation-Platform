"""Integration tests for Phase 3: Evaluation Engine + Metrics."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Shared helpers
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


def _make_prompt(client: TestClient, template: str = "Answer: {question}") -> dict:
    r = client.post(
        "/prompts",
        json={
            "name": "qa",
            "description": "",
            "template": template,
            "input_variables": ["question"],
        },
    )
    assert r.status_code == 201
    return r.json()


def _make_dataset(client: TestClient, items: list | None = None) -> dict:
    if items is None:
        items = [
            {"input": {"question": "What is 2+2?"}, "expected": "4"},
            {"input": {"question": "Capital of France?"}, "expected": "Paris"},
        ]
    r = client.post(
        "/datasets",
        json={"name": "test-ds", "description": "", "items": items, "item_count": len(items)},
    )
    assert r.status_code == 201
    return r.json()


def _make_metric(client: TestClient, kind: str = "exact_match", config: dict | None = None) -> dict:
    r = client.post(
        "/metrics",
        json={"name": f"{kind}-metric", "description": "", "kind": kind, "config": config or {}},
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
    ollama_response: str = "4",
) -> dict:
    with patch("app.services.providers.ollama.httpx.Client", _mock_client(ollama_response)):
        r = client.post(
            "/evaluations",
            json={
                "name": "test-eval",
                "prompt_key": prompt["entity_key"],
                "model_key": model["entity_key"],
                "dataset_key": dataset["entity_key"],
                "metric_keys": [metric["entity_key"]],
                "parameters": {},
            },
        )
    return r


# ---------------------------------------------------------------------------
# Metric CRUD
# ---------------------------------------------------------------------------


def test_metric_create_and_get(client: TestClient) -> None:
    m = _make_metric(client, "exact_match")
    assert m["kind"] == "exact_match"
    assert m["version"] == 1
    assert m["is_latest"] is True

    r = client.get(f"/metrics/{m['entity_key']}")
    assert r.status_code == 200
    assert r.json()["name"] == "exact_match-metric"


def test_metric_revise(client: TestClient) -> None:
    m = _make_metric(client, "contains")
    r = client.post(
        f"/metrics/{m['entity_key']}/versions",
        json={"name": "contains-v2", "description": "revised", "kind": "contains", "config": {}},
    )
    assert r.status_code == 201
    v2 = r.json()
    assert v2["version"] == 2
    assert v2["is_latest"] is True


def test_metric_list(client: TestClient) -> None:
    _make_metric(client, "exact_match")
    _make_metric(client, "contains")
    r = client.get("/metrics")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_metric_not_found(client: TestClient) -> None:
    import uuid

    r = client.get(f"/metrics/{uuid.uuid4()}")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Evaluation execution — exact_match
# ---------------------------------------------------------------------------


def test_evaluation_exact_match_completed(client: TestClient) -> None:
    provider = _make_provider(client)
    model = _make_model(client, provider["entity_key"])
    prompt = _make_prompt(client)
    dataset = _make_dataset(client)
    metric = _make_metric(client, "exact_match")

    r = _run_eval(client, provider, model, prompt, dataset, metric, ollama_response="4")
    assert r.status_code == 201
    ev = r.json()
    assert ev["status"] == "completed"
    assert ev["total_items"] == 2
    assert ev["scored_items"] == 2
    assert ev["error"] is None
    assert len(ev["metric_keys"]) == 1
    assert ev["metric_keys"][0] == metric["entity_key"]

    # Provenance captured
    assert ev["prompt_version_id"] == prompt["id"]
    assert ev["model_version_id"] == model["id"]
    assert ev["dataset_version_id"] == dataset["id"]

    # Aggregate scores present
    agg = ev["aggregate_scores"]
    metric_key = metric["entity_key"]
    assert metric_key in agg
    assert "mean_score" in agg[metric_key]
    assert agg[metric_key]["metric_kind"] == "exact_match"
    assert agg[metric_key]["count"] == 2


def test_evaluation_results_per_item(client: TestClient) -> None:
    provider = _make_provider(client)
    model = _make_model(client, provider["entity_key"])
    prompt = _make_prompt(client)
    dataset = _make_dataset(client)
    metric = _make_metric(client, "exact_match")

    r = _run_eval(client, provider, model, prompt, dataset, metric)
    ev_id = r.json()["id"]

    r2 = client.get(f"/evaluations/{ev_id}/results")
    assert r2.status_code == 200
    results = r2.json()
    # 2 items × 1 metric = 2 results
    assert len(results) == 2
    for res in results:
        assert res["status"] == "scored"
        assert res["confidence"] == "high"
        assert res["metric_kind"] == "exact_match"
        assert res["evaluation_id"] == ev_id
        assert res["score"] in (0.0, 1.0)


def test_evaluation_contains_metric(client: TestClient) -> None:
    provider = _make_provider(client)
    model = _make_model(client, provider["entity_key"])
    prompt = _make_prompt(client)
    dataset = _make_dataset(
        client, [{"input": {"question": "capital of france"}, "expected": "Paris"}]
    )
    metric = _make_metric(client, "contains")

    r = _run_eval(
        client, provider, model, prompt, dataset, metric, ollama_response="The capital is Paris."
    )
    assert r.status_code == 201
    ev = r.json()
    agg = ev["aggregate_scores"][metric["entity_key"]]
    assert agg["mean_score"] == 1.0  # "paris" in "the capital is paris."
    assert agg["metric_kind"] == "contains"


def test_evaluation_semantic_similarity(client: TestClient) -> None:
    provider = _make_provider(client)
    model = _make_model(client, provider["entity_key"])
    prompt = _make_prompt(client)
    dataset = _make_dataset(client, [{"input": {"question": "hello"}, "expected": "hello world"}])
    metric = _make_metric(client, "semantic_similarity", {"threshold": 0.5})

    r = _run_eval(client, provider, model, prompt, dataset, metric, ollama_response="hello world")
    assert r.status_code == 201
    ev = r.json()
    agg = ev["aggregate_scores"][metric["entity_key"]]
    assert agg["metric_kind"] == "semantic_similarity"
    assert agg["mean_score"] == 1.0  # identical text → cosine = 1.0
    assert agg["confidence_distribution"].get("low", 0) == 1


# ---------------------------------------------------------------------------
# Evaluation list / get / filter
# ---------------------------------------------------------------------------


def test_evaluation_list_and_get(client: TestClient) -> None:
    provider = _make_provider(client)
    model = _make_model(client, provider["entity_key"])
    prompt = _make_prompt(client)
    dataset = _make_dataset(client)
    metric = _make_metric(client, "exact_match")

    with patch("app.services.providers.ollama.httpx.Client", _mock_client()):
        r = client.post(
            "/evaluations",
            json={
                "name": "eval-a",
                "prompt_key": prompt["entity_key"],
                "model_key": model["entity_key"],
                "dataset_key": dataset["entity_key"],
                "metric_keys": [metric["entity_key"]],
                "parameters": {},
            },
        )
    ev_id = r.json()["id"]

    r2 = client.get("/evaluations")
    assert r2.status_code == 200
    assert len(r2.json()) == 1

    r3 = client.get(f"/evaluations/{ev_id}")
    assert r3.status_code == 200
    assert r3.json()["id"] == ev_id


def test_evaluation_filter_by_model_key(client: TestClient) -> None:
    provider = _make_provider(client)
    model = _make_model(client, provider["entity_key"])
    prompt = _make_prompt(client)
    dataset = _make_dataset(client)
    metric = _make_metric(client, "exact_match")

    with patch("app.services.providers.ollama.httpx.Client", _mock_client()):
        client.post(
            "/evaluations",
            json={
                "name": "e1",
                "prompt_key": prompt["entity_key"],
                "model_key": model["entity_key"],
                "dataset_key": dataset["entity_key"],
                "metric_keys": [metric["entity_key"]],
                "parameters": {},
            },
        )

    r = client.get(f"/evaluations?model_key={model['entity_key']}")
    assert r.status_code == 200
    assert len(r.json()) == 1

    import uuid

    r2 = client.get(f"/evaluations?model_key={uuid.uuid4()}")
    assert r2.json() == []


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


def test_evaluation_unknown_metric_404(client: TestClient) -> None:
    import uuid

    provider = _make_provider(client)
    model = _make_model(client, provider["entity_key"])
    prompt = _make_prompt(client)
    dataset = _make_dataset(client)

    r = client.post(
        "/evaluations",
        json={
            "name": "bad-metric",
            "prompt_key": prompt["entity_key"],
            "model_key": model["entity_key"],
            "dataset_key": dataset["entity_key"],
            "metric_keys": [str(uuid.uuid4())],
            "parameters": {},
        },
    )
    assert r.status_code == 404


def test_evaluation_empty_dataset_422(client: TestClient) -> None:
    provider = _make_provider(client)
    model = _make_model(client, provider["entity_key"])
    prompt = _make_prompt(client)
    metric = _make_metric(client, "exact_match")
    empty_ds = _make_dataset(client, [])

    r = client.post(
        "/evaluations",
        json={
            "name": "empty",
            "prompt_key": prompt["entity_key"],
            "model_key": model["entity_key"],
            "dataset_key": empty_ds["entity_key"],
            "metric_keys": [metric["entity_key"]],
            "parameters": {},
        },
    )
    assert r.status_code == 422


def test_evaluation_missing_metric_keys_422(client: TestClient) -> None:
    provider = _make_provider(client)
    model = _make_model(client, provider["entity_key"])
    prompt = _make_prompt(client)
    dataset = _make_dataset(client)

    r = client.post(
        "/evaluations",
        json={
            "name": "no-metrics",
            "prompt_key": prompt["entity_key"],
            "model_key": model["entity_key"],
            "dataset_key": dataset["entity_key"],
            "metric_keys": [],
            "parameters": {},
        },
    )
    assert r.status_code == 422


def test_evaluation_404_on_get(client: TestClient) -> None:
    import uuid

    r = client.get(f"/evaluations/{uuid.uuid4()}")
    assert r.status_code == 404


def test_evaluation_results_filter_by_metric(client: TestClient) -> None:
    provider = _make_provider(client)
    model = _make_model(client, provider["entity_key"])
    prompt = _make_prompt(client)
    dataset = _make_dataset(client)
    m1 = _make_metric(client, "exact_match")
    m2 = _make_metric(client, "contains")

    with patch("app.services.providers.ollama.httpx.Client", _mock_client("4")):
        r = client.post(
            "/evaluations",
            json={
                "name": "multi-metric",
                "prompt_key": prompt["entity_key"],
                "model_key": model["entity_key"],
                "dataset_key": dataset["entity_key"],
                "metric_keys": [m1["entity_key"], m2["entity_key"]],
                "parameters": {},
            },
        )
    ev_id = r.json()["id"]

    # 2 items × 2 metrics = 4 results total
    all_results = client.get(f"/evaluations/{ev_id}/results").json()
    assert len(all_results) == 4

    # Filter to just m1
    filtered = client.get(f"/evaluations/{ev_id}/results?metric_key={m1['entity_key']}").json()
    assert len(filtered) == 2
    assert all(res["metric_kind"] == "exact_match" for res in filtered)
