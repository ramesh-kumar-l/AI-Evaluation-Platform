"""Evaluations API: execute dataset-level evaluations and retrieve results."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_actor
from app.core.database import get_db
from app.models.dataset import Dataset
from app.models.evaluation import Evaluation
from app.models.evaluation_result import EvaluationResult
from app.models.metric import Metric
from app.models.prompt import Prompt
from app.models.provider import Model, Provider
from app.schemas.evaluation import EvaluationCreate, EvaluationOut, EvaluationResultOut
from app.services.evaluation_service import EvaluationError, execute_evaluation
from app.services.versioning import get_latest, get_version

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


def _resolve_prompt(db: Session, key: uuid.UUID, version: int | None) -> Prompt:
    entity = get_version(db, Prompt, key, version) if version else get_latest(db, Prompt, key)
    if entity is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Prompt {key} not found")
    return entity


def _resolve_model(db: Session, key: uuid.UUID, version: int | None) -> Model:
    entity = get_version(db, Model, key, version) if version else get_latest(db, Model, key)
    if entity is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Model {key} not found")
    return entity


def _resolve_dataset(db: Session, key: uuid.UUID, version: int | None) -> Dataset:
    entity = get_version(db, Dataset, key, version) if version else get_latest(db, Dataset, key)
    if entity is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Dataset {key} not found")
    return entity


def _resolve_metrics(db: Session, keys: list[uuid.UUID]) -> list[Metric]:
    metrics: list[Metric] = []
    for key in keys:
        m = get_latest(db, Metric, key)
        if m is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Metric {key} not found")
        metrics.append(m)
    return metrics


@router.post("", response_model=EvaluationOut, status_code=status.HTTP_201_CREATED)
def create_evaluation(
    body: EvaluationCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[str, Depends(get_actor)],
) -> EvaluationOut:
    prompt = _resolve_prompt(db, body.prompt_key, body.prompt_version)
    model = _resolve_model(db, body.model_key, body.model_version)
    provider = get_latest(db, Provider, model.provider_key)
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Provider for model not found")
    dataset = _resolve_dataset(db, body.dataset_key, body.dataset_version)
    metric_rows = _resolve_metrics(db, body.metric_keys)

    try:
        evaluation = execute_evaluation(
            db,
            name=body.name,
            prompt=prompt,
            model=model,
            provider=provider,
            dataset=dataset,
            metric_rows=metric_rows,
            parameters=body.parameters,
            actor=actor,
        )
    except EvaluationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return EvaluationOut.model_validate(evaluation)


@router.get("", response_model=list[EvaluationOut])
def list_evaluations(
    db: Annotated[Session, Depends(get_db)],
    dataset_key: Annotated[uuid.UUID | None, Query()] = None,
    model_key: Annotated[uuid.UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[EvaluationOut]:
    stmt = select(Evaluation).order_by(Evaluation.created_at.desc()).limit(limit)
    if dataset_key is not None:
        stmt = stmt.where(Evaluation.dataset_key == dataset_key)
    if model_key is not None:
        stmt = stmt.where(Evaluation.model_key == model_key)
    rows = list(db.execute(stmt).scalars().all())
    return [EvaluationOut.model_validate(r) for r in rows]


@router.get("/{evaluation_id}", response_model=EvaluationOut)
def get_evaluation(
    evaluation_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> EvaluationOut:
    ev = db.get(Evaluation, evaluation_id)
    if ev is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"Evaluation {evaluation_id} not found"
        )
    return EvaluationOut.model_validate(ev)


@router.get("/{evaluation_id}/results", response_model=list[EvaluationResultOut])
def list_results(
    evaluation_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    metric_key: Annotated[uuid.UUID | None, Query()] = None,
) -> list[EvaluationResultOut]:
    ev = db.get(Evaluation, evaluation_id)
    if ev is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"Evaluation {evaluation_id} not found"
        )
    stmt = (
        select(EvaluationResult)
        .where(EvaluationResult.evaluation_id == evaluation_id)
        .order_by(EvaluationResult.item_index)
    )
    if metric_key is not None:
        stmt = stmt.where(EvaluationResult.metric_key == metric_key)
    rows = list(db.execute(stmt).scalars().all())
    return [EvaluationResultOut.model_validate(r) for r in rows]
