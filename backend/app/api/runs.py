"""Runs API: execute inference and retrieve run records."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_actor
from app.core.database import get_db
from app.models.prompt import Prompt
from app.models.provider import Model, Provider
from app.models.run import InferenceRun
from app.schemas.run import RunCreate, RunOut
from app.services.run_service import RunError, execute_run
from app.services.versioning import get_latest, get_version

router = APIRouter(prefix="/runs", tags=["runs"])


def _get_prompt(db: Session, key: uuid.UUID, version: int | None) -> Prompt:
    entity: Prompt | None = (
        get_version(db, Prompt, key, version)
        if version is not None
        else get_latest(db, Prompt, key)
    )
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prompt {key} not found")
    return entity


def _get_model(db: Session, key: uuid.UUID, version: int | None) -> Model:
    entity: Model | None = (
        get_version(db, Model, key, version) if version is not None else get_latest(db, Model, key)
    )
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Model {key} not found")
    return entity


@router.post("", response_model=RunOut, status_code=status.HTTP_201_CREATED)
def create_run(
    body: RunCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[str, Depends(get_actor)],
) -> RunOut:
    prompt = _get_prompt(db, body.prompt_key, body.prompt_version)
    model = _get_model(db, body.model_key, body.model_version)

    provider: Provider | None = get_latest(db, Provider, model.provider_key)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider for model {body.model_key} not found",
        )

    try:
        run = execute_run(
            db,
            prompt=prompt,
            model=model,
            provider=provider,
            input_variables=body.input_variables,
            parameters=body.parameters,
            actor=actor,
        )
    except RunError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return RunOut.model_validate(run)


@router.get("", response_model=list[RunOut])
def list_runs(
    db: Annotated[Session, Depends(get_db)],
    prompt_key: Annotated[uuid.UUID | None, Query()] = None,
    model_key: Annotated[uuid.UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[RunOut]:
    stmt = select(InferenceRun).order_by(InferenceRun.created_at.desc()).limit(limit)
    if prompt_key is not None:
        stmt = stmt.where(InferenceRun.prompt_key == prompt_key)
    if model_key is not None:
        stmt = stmt.where(InferenceRun.model_key == model_key)
    rows = list(db.execute(stmt).scalars().all())
    return [RunOut.model_validate(r) for r in rows]


@router.get("/{run_id}", response_model=RunOut)
def get_run(
    run_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> RunOut:
    run = db.get(InferenceRun, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found",
        )
    return RunOut.model_validate(run)
