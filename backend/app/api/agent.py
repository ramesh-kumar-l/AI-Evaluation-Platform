"""Agent & Tool Evaluation API — /agent prefix."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.agent_eval import AgentEval
from app.models.agent_eval_result import AgentEvalResult
from app.models.agent_run import AgentRun
from app.models.agent_step import AgentStep
from app.schemas.agent import (
    AgentEvalCreate,
    AgentEvalOut,
    AgentEvalResultOut,
    AgentRunCreate,
    AgentRunOut,
    AgentStepOut,
)
from app.services.agent_eval_service import run_agent_eval
from app.services.agent_run_service import (
    AgentError,
    create_run,
    get_run,
    list_runs,
    list_steps,
)

router = APIRouter(prefix="/agent", tags=["agent"])

DbDep = Annotated[Session, Depends(get_db)]
_ACTOR = "api"


# ---------------------------------------------------------------------------
# Agent Runs
# ---------------------------------------------------------------------------


@router.post("/runs", response_model=AgentRunOut, status_code=201)
def submit_run(body: AgentRunCreate, db: DbDep) -> AgentRun:
    return create_run(
        db,
        agent_name=body.agent_name,
        query=body.query,
        final_answer=body.final_answer,
        tool_calls=body.tool_calls,
        status=body.status,
        steps=[s.model_dump() for s in body.steps],
        actor=_ACTOR,
    )


@router.get("/runs", response_model=list[AgentRunOut])
def get_runs(
    db: DbDep,
    agent_name: str | None = Query(None),
    status: str | None = Query(None),
) -> list[AgentRun]:
    return list_runs(db, agent_name=agent_name, status=status)


@router.get("/runs/{run_id}", response_model=AgentRunOut)
def get_run_by_id(run_id: uuid.UUID, db: DbDep) -> AgentRun:
    run = get_run(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return run


@router.get("/runs/{run_id}/steps", response_model=list[AgentStepOut])
def get_run_steps(run_id: uuid.UUID, db: DbDep) -> list[AgentStep]:
    if get_run(db, run_id) is None:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return list_steps(db, run_id)


# ---------------------------------------------------------------------------
# Agent Evaluations
# ---------------------------------------------------------------------------


@router.post("/evaluations", response_model=AgentEvalOut, status_code=201)
def create_eval(body: AgentEvalCreate, db: DbDep) -> AgentEval:
    try:
        return run_agent_eval(
            db,
            dataset_key=body.dataset_key,
            agent_name=body.agent_name,
            actor=_ACTOR,
        )
    except AgentError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/evaluations", response_model=list[AgentEvalOut])
def list_evals(
    db: DbDep,
    agent_name: str | None = Query(None),
) -> list[AgentEval]:
    stmt = select(AgentEval)
    if agent_name:
        stmt = stmt.where(AgentEval.agent_name == agent_name)
    return list(db.execute(stmt.order_by(AgentEval.created_at.desc())).scalars().all())


@router.get("/evaluations/{eval_id}", response_model=AgentEvalOut)
def get_eval_by_id(eval_id: uuid.UUID, db: DbDep) -> AgentEval:
    ev = db.get(AgentEval, eval_id)
    if ev is None:
        raise HTTPException(status_code=404, detail="Agent evaluation not found")
    return ev


@router.get("/evaluations/{eval_id}/results", response_model=list[AgentEvalResultOut])
def get_eval_results(eval_id: uuid.UUID, db: DbDep) -> list[AgentEvalResult]:
    stmt = (
        select(AgentEvalResult)
        .where(AgentEvalResult.agent_eval_id == eval_id)
        .order_by(AgentEvalResult.created_at)
    )
    return list(db.execute(stmt).scalars().all())
