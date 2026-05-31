"""Agent evaluation service: score agent runs against dataset expectations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent_eval import AgentEval
from app.models.agent_eval_result import AgentEvalResult
from app.models.agent_run import AgentRun
from app.models.dataset import Dataset
from app.services import audit
from app.services.agent_run_service import AgentError
from app.services.metrics.task_completion import score_task_completion
from app.services.metrics.tool_call_accuracy import score_tool_call_accuracy
from app.services.metrics.trajectory_score import score_trajectory
from app.services.versioning import get_latest


def _extract_query(item: Any) -> str:
    if isinstance(item, dict):
        inp = item.get("input", "")
        if isinstance(inp, dict):
            return str(inp.get("query", inp.get("text", str(inp))))
        return str(inp)
    return str(item)


def _extract_expected_answer(item: Any) -> str:
    """Extract expected answer — supports both plain string and dict expected."""
    if isinstance(item, dict):
        expected = item.get("expected", "")
        if isinstance(expected, dict):
            return str(expected.get("answer", ""))
        return str(expected)
    return ""


def _extract_expected_tools(item: Any) -> list[str]:
    """Extract expected tool list from expected.tools dict format.

    Dataset items store agent-specific metadata inside 'expected' as a dict
    because DatasetItem schema only carries input/expected fields:
      {"input": "query", "expected": {"answer": "...", "tools": ["t1"]}}
    """
    if isinstance(item, dict):
        expected = item.get("expected", "")
        if isinstance(expected, dict):
            tools = expected.get("tools", [])
            if isinstance(tools, list):
                return [str(t) for t in tools]
    return []


def _find_run(db: Session, agent_name: str, query: str) -> AgentRun | None:
    """Find the most recent completed run for this agent_name + query."""
    stmt = (
        select(AgentRun)
        .where(AgentRun.agent_name == agent_name, AgentRun.query == query)
        .order_by(AgentRun.created_at.desc())
        .limit(1)
    )
    return db.execute(stmt).scalars().first()


def run_agent_eval(
    db: Session,
    *,
    dataset_key: uuid.UUID,
    agent_name: str,
    actor: str,
) -> AgentEval:
    """Score all dataset items by matching agent runs; produce AgentEval + results."""
    dataset = get_latest(db, Dataset, dataset_key)
    if dataset is None:
        raise AgentError(f"Dataset {dataset_key} not found")

    items: list[Any] = dataset.items
    now = datetime.now(UTC)

    agent_eval = AgentEval(
        id=uuid.uuid4(),
        dataset_key=dataset.entity_key,
        agent_name=agent_name,
        query_count=0,
        mean_tool_accuracy=0.0,
        mean_trajectory_score=0.0,
        mean_task_completion=0.0,
        status="completed",
        created_at=now,
        created_by=actor,
    )
    db.add(agent_eval)
    db.flush()

    result_rows: list[AgentEvalResult] = []
    for item in items:
        query = _extract_query(item)
        exp_answer = _extract_expected_answer(item)
        exp_tools = _extract_expected_tools(item)

        run = _find_run(db, agent_name, query)
        actual_answer = run.final_answer if run else ""
        actual_tools = (
            [str(tc.get("name", "")) for tc in run.tool_calls if isinstance(tc, dict)]
            if run
            else []
        )

        tool_acc = score_tool_call_accuracy(exp_tools, actual_tools)
        traj = score_trajectory(exp_tools, actual_tools)
        task = score_task_completion(exp_answer, actual_answer)

        row = AgentEvalResult(
            id=uuid.uuid4(),
            agent_eval_id=agent_eval.id,
            query_text=query,
            expected_answer=exp_answer,
            actual_answer=actual_answer,
            expected_tools=exp_tools,
            actual_tools=actual_tools,
            tool_call_accuracy=tool_acc,
            trajectory_score=traj,
            task_completion_score=task,
            created_at=now,
        )
        db.add(row)
        result_rows.append(row)

    n = len(result_rows)
    agent_eval.query_count = n
    agent_eval.status = "completed" if n > 0 else "failed"
    if n > 0:
        agent_eval.mean_tool_accuracy = round(sum(r.tool_call_accuracy for r in result_rows) / n, 4)
        agent_eval.mean_trajectory_score = round(
            sum(r.trajectory_score for r in result_rows) / n, 4
        )
        agent_eval.mean_task_completion = round(
            sum(r.task_completion_score for r in result_rows) / n, 4
        )

    db.flush()
    audit.record_event(
        db,
        actor=actor,
        action="create",
        entity_type="agent_evals",
        entity_key=agent_eval.id,
        entity_version_id=None,
        payload={
            "dataset_key": str(dataset_key),
            "agent_name": agent_name,
            "query_count": n,
            "status": agent_eval.status,
        },
    )
    db.commit()
    db.refresh(agent_eval)
    return agent_eval
