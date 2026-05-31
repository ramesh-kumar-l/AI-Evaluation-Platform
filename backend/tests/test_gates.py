"""Integration tests for Phase 6: Release Gates & Approvals."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers (replicated from test_comparisons to keep tests self-contained)
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


def _make_comparison(client: TestClient, baseline_id: str, candidate_id: str) -> dict:
    r = client.post(
        "/comparisons",
        json={
            "name": "test-comp",
            "baseline_id": baseline_id,
            "candidate_id": candidate_id,
            "kind": "generic",
            "threshold_config": {},
        },
    )
    assert r.status_code == 201
    return r.json()


def _setup_neutral_comparison(client: TestClient) -> tuple[dict, str]:
    """Create a neutral comparison (both evals score 0.5). Returns (metric, comparison_id)."""
    prov = _make_provider(client)
    model = _make_model(client, prov["entity_key"])
    prompt = _make_prompt(client)
    ds = _make_dataset(client)
    metric = _make_metric(client)
    baseline = _run_eval(client, prov, model, prompt, ds, metric, "4", "baseline")
    candidate = _run_eval(client, prov, model, prompt, ds, metric, "4", "candidate")
    comp = _make_comparison(client, baseline["id"], candidate["id"])
    return metric, comp["id"]


def _setup_regression_comparison(client: TestClient) -> tuple[dict, str]:
    """Create a comparison with 1 regression. Returns (metric, comparison_id)."""
    prov = _make_provider(client)
    model = _make_model(client, prov["entity_key"])
    prompt = _make_prompt(client)
    ds = _make_dataset(client)
    metric = _make_metric(client)
    # baseline scores 0.5; candidate scores 0.0 → regression
    baseline = _run_eval(client, prov, model, prompt, ds, metric, "4", "baseline")
    candidate = _run_eval(client, prov, model, prompt, ds, metric, "zzz_wrong", "candidate")
    comp = _make_comparison(client, baseline["id"], candidate["id"])
    return metric, comp["id"]


# ---------------------------------------------------------------------------
# Gate CRUD tests
# ---------------------------------------------------------------------------


def test_gate_create(client: TestClient) -> None:
    """Create a gate and verify all fields are persisted."""
    r = client.post(
        "/gates",
        json={
            "name": "quality-gate",
            "description": "Must score 80%+",
            "criteria": [{"metric_key": "exact_match", "min_score": 0.8}],
            "max_regressions_allowed": 0,
            "require_approval": False,
        },
    )
    assert r.status_code == 201
    gate = r.json()
    assert gate["name"] == "quality-gate"
    assert gate["version"] == 1
    assert gate["is_latest"] is True
    assert gate["max_regressions_allowed"] == 0
    assert gate["require_approval"] is False
    assert len(gate["criteria"]) == 1
    assert gate["criteria"][0]["min_score"] == 0.8


def test_gate_list(client: TestClient) -> None:
    """List returns the latest version of all gates."""
    client.post("/gates", json={"name": "gate-a", "criteria": [], "require_approval": False})
    client.post("/gates", json={"name": "gate-b", "criteria": [], "require_approval": True})
    r = client.get("/gates")
    assert r.status_code == 200
    names = {g["name"] for g in r.json()}
    assert {"gate-a", "gate-b"} == names


def test_gate_get_not_found(client: TestClient) -> None:
    """Unknown gate_key returns 404."""
    r = client.get(f"/gates/{uuid.uuid4()}")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Gate evaluation tests
# ---------------------------------------------------------------------------


def test_gate_evaluate_passed(client: TestClient) -> None:
    """All criteria satisfied, no regressions, require_approval=False → passed."""
    metric, comp_id = _setup_neutral_comparison(client)
    r = client.post(
        "/gates",
        json={
            "name": "permissive-gate",
            "criteria": [{"metric_key": metric["entity_key"], "min_score": 0.0}],
            "max_regressions_allowed": 0,
            "require_approval": False,
        },
    )
    gate_key = r.json()["entity_key"]

    r2 = client.post(f"/gates/{gate_key}/evaluate", json={"comparison_id": comp_id})
    assert r2.status_code == 201
    decision = r2.json()
    assert decision["status"] == "passed"
    assert decision["criteria_passed"] == 1
    assert decision["criteria_failed"] == 0


def test_gate_evaluate_pending_approval(client: TestClient) -> None:
    """All criteria satisfied, require_approval=True → pending_approval."""
    metric, comp_id = _setup_neutral_comparison(client)
    r = client.post(
        "/gates",
        json={
            "name": "approval-gate",
            "criteria": [{"metric_key": metric["entity_key"], "min_score": 0.0}],
            "max_regressions_allowed": 0,
            "require_approval": True,
        },
    )
    gate_key = r.json()["entity_key"]

    r2 = client.post(f"/gates/{gate_key}/evaluate", json={"comparison_id": comp_id})
    assert r2.status_code == 201
    assert r2.json()["status"] == "pending_approval"


def test_gate_evaluate_failed_criterion(client: TestClient) -> None:
    """min_score=1.0 when candidate scores 0.5 → criterion fails → failed."""
    metric, comp_id = _setup_neutral_comparison(client)
    r = client.post(
        "/gates",
        json={
            "name": "strict-gate",
            "criteria": [{"metric_key": metric["entity_key"], "min_score": 1.0}],
            "max_regressions_allowed": 0,
            "require_approval": False,
        },
    )
    gate_key = r.json()["entity_key"]

    r2 = client.post(f"/gates/{gate_key}/evaluate", json={"comparison_id": comp_id})
    assert r2.status_code == 201
    decision = r2.json()
    assert decision["status"] == "failed"
    assert decision["criteria_failed"] == 1
    assert decision["criteria_passed"] == 0


def test_gate_evaluate_failed_regressions(client: TestClient) -> None:
    """regressions_detected=1 with max_regressions_allowed=0 → failed."""
    metric, comp_id = _setup_regression_comparison(client)
    r = client.post(
        "/gates",
        json={
            "name": "no-regression-gate",
            "criteria": [{"metric_key": metric["entity_key"], "min_score": 0.0}],
            "max_regressions_allowed": 0,
            "require_approval": False,
        },
    )
    gate_key = r.json()["entity_key"]

    r2 = client.post(f"/gates/{gate_key}/evaluate", json={"comparison_id": comp_id})
    assert r2.status_code == 201
    decision = r2.json()
    assert decision["status"] == "failed"
    assert decision["regressions_detected"] >= 1


def test_gate_evaluate_missing_comparison_422(client: TestClient) -> None:
    """Comparison not found → 422."""
    r = client.post(
        "/gates",
        json={"name": "g", "criteria": [], "require_approval": False},
    )
    gate_key = r.json()["entity_key"]

    r2 = client.post(f"/gates/{gate_key}/evaluate", json={"comparison_id": str(uuid.uuid4())})
    assert r2.status_code == 422


def test_gate_evaluate_records_audit_event(client: TestClient) -> None:
    """Evaluating a gate produces an audit event with action='evaluate'."""
    metric, comp_id = _setup_neutral_comparison(client)
    r = client.post(
        "/gates",
        json={
            "name": "audited-gate",
            "criteria": [{"metric_key": metric["entity_key"], "min_score": 0.0}],
            "require_approval": False,
        },
    )
    gate_key = r.json()["entity_key"]
    client.post(f"/gates/{gate_key}/evaluate", json={"comparison_id": comp_id})

    audit = client.get("/audit/events").json()
    actions = [e["action"] for e in audit]
    assert "evaluate" in actions


# ---------------------------------------------------------------------------
# Approval tests
# ---------------------------------------------------------------------------


def test_gate_approve_pending(client: TestClient) -> None:
    """Approve a pending_approval decision → status becomes approved."""
    metric, comp_id = _setup_neutral_comparison(client)
    r = client.post(
        "/gates",
        json={
            "name": "approval-gate",
            "criteria": [{"metric_key": metric["entity_key"], "min_score": 0.0}],
            "require_approval": True,
        },
    )
    gate_key = r.json()["entity_key"]
    decision = client.post(f"/gates/{gate_key}/evaluate", json={"comparison_id": comp_id}).json()
    assert decision["status"] == "pending_approval"

    r2 = client.post(
        f"/gates/decisions/{decision['id']}/approve",
        json={"action": "approved", "justification": "All checks look good, approved for release."},
    )
    assert r2.status_code == 201
    approval = r2.json()
    assert approval["action"] == "approved"

    # Decision status should now be approved
    decisions = client.get(f"/gates/{gate_key}/decisions").json()
    assert decisions[0]["status"] == "approved"


def test_gate_reject_pending(client: TestClient) -> None:
    """Reject a pending_approval decision → status becomes rejected."""
    metric, comp_id = _setup_neutral_comparison(client)
    r = client.post(
        "/gates",
        json={
            "name": "reject-gate",
            "criteria": [{"metric_key": metric["entity_key"], "min_score": 0.0}],
            "require_approval": True,
        },
    )
    gate_key = r.json()["entity_key"]
    decision = client.post(f"/gates/{gate_key}/evaluate", json={"comparison_id": comp_id}).json()

    r2 = client.post(
        f"/gates/decisions/{decision['id']}/approve",
        json={"action": "rejected", "justification": "Scores are insufficient for production."},
    )
    assert r2.status_code == 201
    assert r2.json()["action"] == "rejected"

    decisions = client.get(f"/gates/{gate_key}/decisions").json()
    assert decisions[0]["status"] == "rejected"


def test_gate_override_failed(client: TestClient) -> None:
    """Override a failed decision with justification → status becomes overridden."""
    metric, comp_id = _setup_regression_comparison(client)
    r = client.post(
        "/gates",
        json={
            "name": "override-gate",
            "criteria": [{"metric_key": metric["entity_key"], "min_score": 0.0}],
            "max_regressions_allowed": 0,
            "require_approval": False,
        },
    )
    gate_key = r.json()["entity_key"]
    decision = client.post(f"/gates/{gate_key}/evaluate", json={"comparison_id": comp_id}).json()
    assert decision["status"] == "failed"

    r2 = client.post(
        f"/gates/decisions/{decision['id']}/approve",
        json={
            "action": "overridden",
            "justification": "Regression is in non-critical path; approved with exception.",
        },
    )
    assert r2.status_code == 201
    assert r2.json()["action"] == "overridden"

    decisions = client.get(f"/gates/{gate_key}/decisions").json()
    assert decisions[0]["status"] == "overridden"
    assert decisions[0]["override"] is True


def test_gate_invalid_approval_action_422(client: TestClient) -> None:
    """Trying to approve a 'passed' decision → 422 (wrong status transition)."""
    metric, comp_id = _setup_neutral_comparison(client)
    r = client.post(
        "/gates",
        json={
            "name": "no-approval-gate",
            "criteria": [{"metric_key": metric["entity_key"], "min_score": 0.0}],
            "require_approval": False,
        },
    )
    gate_key = r.json()["entity_key"]
    decision = client.post(f"/gates/{gate_key}/evaluate", json={"comparison_id": comp_id}).json()
    assert decision["status"] == "passed"

    # Cannot approve a "passed" decision — it has no pending_approval status
    r2 = client.post(
        f"/gates/decisions/{decision['id']}/approve",
        json={"action": "approved", "justification": "This should not be valid."},
    )
    assert r2.status_code == 422


def test_gate_decision_not_found_404(client: TestClient) -> None:
    """Approving a non-existent decision → 404."""
    r = client.post(
        f"/gates/decisions/{uuid.uuid4()}/approve",
        json={"action": "approved", "justification": "Does not matter at all."},
    )
    assert r.status_code == 404


def test_gate_list_decisions(client: TestClient) -> None:
    """List decisions for a gate returns all of them in descending order."""
    metric, comp_id = _setup_neutral_comparison(client)
    r = client.post(
        "/gates",
        json={
            "name": "multi-eval-gate",
            "criteria": [{"metric_key": metric["entity_key"], "min_score": 0.0}],
            "require_approval": False,
        },
    )
    gate_key = r.json()["entity_key"]

    # Run two evaluations against the same gate
    client.post(f"/gates/{gate_key}/evaluate", json={"comparison_id": comp_id})
    client.post(f"/gates/{gate_key}/evaluate", json={"comparison_id": comp_id})

    decisions = client.get(f"/gates/{gate_key}/decisions").json()
    assert len(decisions) == 2
    # All decisions belong to this gate
    assert all(d["gate_key"] == gate_key for d in decisions)
