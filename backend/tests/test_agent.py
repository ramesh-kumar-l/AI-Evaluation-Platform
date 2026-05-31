"""Phase 9 — Agent & Tool Evaluation tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.services.metrics.task_completion import score_task_completion
from app.services.metrics.tool_call_accuracy import score_tool_call_accuracy
from app.services.metrics.trajectory_score import score_trajectory

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_dataset(client: TestClient, items: list[dict]) -> dict:
    ds = client.post(
        "/datasets",
        json={"name": "agent-ds", "description": "test", "items": items},
    ).json()
    return ds


def _submit_run(
    client: TestClient,
    *,
    agent_name: str,
    query: str,
    final_answer: str = "",
    tool_calls: list[dict] | None = None,
    steps: list[dict] | None = None,
    status: str = "completed",
) -> dict:
    return client.post(
        "/agent/runs",
        json={
            "agent_name": agent_name,
            "query": query,
            "final_answer": final_answer,
            "tool_calls": tool_calls or [],
            "steps": steps or [],
            "status": status,
        },
    ).json()


# ---------------------------------------------------------------------------
# Metric scorer unit tests
# ---------------------------------------------------------------------------


def test_tool_call_accuracy_perfect() -> None:
    assert score_tool_call_accuracy(["search", "calc"], ["search", "calc"]) == 1.0


def test_tool_call_accuracy_partial() -> None:
    score = score_tool_call_accuracy(["search", "calc", "db"], ["search", "calc"])
    assert 0.0 < score < 1.0


def test_tool_call_accuracy_both_empty() -> None:
    assert score_tool_call_accuracy([], []) == 1.0


def test_tool_call_accuracy_one_empty() -> None:
    assert score_tool_call_accuracy(["search"], []) == 0.0


def test_trajectory_score_perfect() -> None:
    assert score_trajectory(["a", "b", "c"], ["a", "b", "c"]) == 1.0


def test_trajectory_score_partial() -> None:
    score = score_trajectory(["a", "b", "c"], ["a", "c"])
    assert 0.0 < score < 1.0


def test_trajectory_score_both_empty() -> None:
    assert score_trajectory([], []) == 1.0


def test_task_completion_identical() -> None:
    score = score_task_completion("Paris is the capital", "Paris is the capital")
    assert score == 1.0


def test_task_completion_empty() -> None:
    assert score_task_completion("", "answer") == 0.0


def test_task_completion_unrelated() -> None:
    # TF-cosine shares stop words ("is", "the"), so threshold is loose
    score = score_task_completion("Paris capital France", "sky blue clouds")
    assert score < 0.1


# ---------------------------------------------------------------------------
# Agent Run CRUD
# ---------------------------------------------------------------------------


def test_submit_run(client: TestClient) -> None:
    run = _submit_run(
        client,
        agent_name="test-agent",
        query="What is 2+2?",
        final_answer="4",
        tool_calls=[{"name": "calc", "input": "2+2", "output": "4"}],
        steps=[
            {
                "step_index": 0,
                "step_type": "tool_call",
                "tool_name": "calc",
                "tool_input": {"expr": "2+2"},
                "tool_output": "4",
            }
        ],
    )
    assert run["agent_name"] == "test-agent"
    assert run["step_count"] == 1
    assert run["status"] == "completed"


def test_get_run_by_id(client: TestClient) -> None:
    run = _submit_run(client, agent_name="agent-a", query="Q1")
    resp = client.get(f"/agent/runs/{run['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == run["id"]


def test_get_run_not_found(client: TestClient) -> None:
    resp = client.get("/agent/runs/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_list_runs_filter_by_agent_name(client: TestClient) -> None:
    _submit_run(client, agent_name="filter-agent", query="Q1")
    _submit_run(client, agent_name="filter-agent", query="Q2")
    _submit_run(client, agent_name="other-agent", query="Q3")
    runs = client.get("/agent/runs?agent_name=filter-agent").json()
    assert all(r["agent_name"] == "filter-agent" for r in runs)
    assert len(runs) >= 2


def test_get_run_steps(client: TestClient) -> None:
    run = _submit_run(
        client,
        agent_name="step-agent",
        query="Multi-step query",
        steps=[
            {"step_index": 0, "step_type": "thinking", "reasoning_text": "Let me think"},
            {"step_index": 1, "step_type": "tool_call", "tool_name": "search"},
        ],
    )
    steps = client.get(f"/agent/runs/{run['id']}/steps").json()
    assert len(steps) == 2
    assert steps[0]["step_type"] == "thinking"
    assert steps[1]["step_type"] == "tool_call"


# ---------------------------------------------------------------------------
# Agent Evaluation
# ---------------------------------------------------------------------------


def test_agent_eval_end_to_end(client: TestClient) -> None:
    # expected is a dict so DatasetItem schema preserves answer + tools
    items = [
        {
            "input": "capital of France",
            "expected": {"answer": "Paris", "tools": ["search"]},
        },
        {
            "input": "capital of Germany",
            "expected": {"answer": "Berlin", "tools": ["search"]},
        },
    ]
    ds = _make_dataset(client, items)
    _submit_run(
        client,
        agent_name="geo-agent",
        query="capital of France",
        final_answer="Paris",
        tool_calls=[{"name": "search", "input": "France capital", "output": "Paris"}],
    )
    _submit_run(
        client,
        agent_name="geo-agent",
        query="capital of Germany",
        final_answer="Berlin",
        tool_calls=[{"name": "search", "input": "Germany capital", "output": "Berlin"}],
    )
    ev = client.post(
        "/agent/evaluations",
        json={"dataset_key": ds["entity_key"], "agent_name": "geo-agent"},
    ).json()
    assert ev["query_count"] == 2
    assert ev["status"] == "completed"
    assert ev["mean_task_completion"] > 0.5
    assert ev["mean_tool_accuracy"] == 1.0


def test_agent_eval_no_runs_scores_zero(client: TestClient) -> None:
    items = [{"input": "Q with no run", "expected": {"answer": "ans", "tools": ["tool1"]}}]
    ds = _make_dataset(client, items)
    ev = client.post(
        "/agent/evaluations",
        json={"dataset_key": ds["entity_key"], "agent_name": "ghost-agent"},
    ).json()
    assert ev["mean_tool_accuracy"] == 0.0
    assert ev["mean_task_completion"] == 0.0


def test_agent_eval_results(client: TestClient) -> None:
    items = [{"input": "test query", "expected": {"answer": "test answer", "tools": []}}]
    ds = _make_dataset(client, items)
    _submit_run(
        client,
        agent_name="res-agent",
        query="test query",
        final_answer="test answer",
    )
    ev = client.post(
        "/agent/evaluations",
        json={"dataset_key": ds["entity_key"], "agent_name": "res-agent"},
    ).json()
    results = client.get(f"/agent/evaluations/{ev['id']}/results").json()
    assert len(results) == 1
    assert results[0]["query_text"] == "test query"
    assert results[0]["task_completion_score"] == 1.0


def test_agent_eval_dataset_not_found(client: TestClient) -> None:
    resp = client.post(
        "/agent/evaluations",
        json={
            "dataset_key": "00000000-0000-0000-0000-000000000000",
            "agent_name": "x",
        },
    )
    assert resp.status_code == 422


def test_agent_eval_list(client: TestClient) -> None:
    items = [{"input": "q", "expected": "a"}]
    ds = _make_dataset(client, items)
    client.post(
        "/agent/evaluations",
        json={"dataset_key": ds["entity_key"], "agent_name": "list-agent"},
    )
    evals = client.get("/agent/evaluations?agent_name=list-agent").json()
    assert len(evals) >= 1


def test_agent_eval_not_found(client: TestClient) -> None:
    resp = client.get("/agent/evaluations/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
