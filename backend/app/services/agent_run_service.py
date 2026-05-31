"""Agent run service: persist agent trajectories and their steps."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent_run import AgentRun
from app.models.agent_step import AgentStep
from app.services import audit


class AgentError(Exception):
    """Domain error for agent-related validation failures."""


def create_run(
    db: Session,
    *,
    agent_name: str,
    query: str,
    final_answer: str,
    tool_calls: list[dict[str, Any]],
    status: str,
    steps: list[dict[str, Any]],
    actor: str,
) -> AgentRun:
    now = datetime.now(UTC)
    run = AgentRun(
        id=uuid.uuid4(),
        agent_name=agent_name,
        query=query,
        final_answer=final_answer,
        tool_calls=tool_calls,
        step_count=len(steps),
        status=status,
        created_at=now,
        created_by=actor,
    )
    db.add(run)
    db.flush()

    for s in steps:
        db.add(
            AgentStep(
                id=uuid.uuid4(),
                agent_run_id=run.id,
                step_index=s.get("step_index", 0),
                step_type=s.get("step_type", "tool_call"),
                tool_name=s.get("tool_name", ""),
                tool_input=s.get("tool_input", {}),
                tool_output=s.get("tool_output", ""),
                reasoning_text=s.get("reasoning_text", ""),
                created_at=now,
            )
        )

    audit.record_event(
        db,
        actor=actor,
        action="create",
        entity_type="agent_runs",
        entity_key=run.id,
        entity_version_id=None,
        payload={
            "agent_name": agent_name,
            "step_count": len(steps),
            "status": status,
        },
    )
    db.commit()
    db.refresh(run)
    return run


def get_run(db: Session, run_id: uuid.UUID) -> AgentRun | None:
    return db.get(AgentRun, run_id)


def list_runs(
    db: Session,
    *,
    agent_name: str | None = None,
    status: str | None = None,
) -> list[AgentRun]:
    stmt = select(AgentRun)
    if agent_name:
        stmt = stmt.where(AgentRun.agent_name == agent_name)
    if status:
        stmt = stmt.where(AgentRun.status == status)
    return list(db.execute(stmt.order_by(AgentRun.created_at.desc())).scalars().all())


def list_steps(db: Session, run_id: uuid.UUID) -> list[AgentStep]:
    stmt = select(AgentStep).where(AgentStep.agent_run_id == run_id).order_by(AgentStep.step_index)
    return list(db.execute(stmt).scalars().all())
