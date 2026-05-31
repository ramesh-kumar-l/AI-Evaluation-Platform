"""Metrics API: versioned CRUD for Metric definitions."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_actor
from app.core.database import get_db
from app.models.metric import Metric
from app.schemas.metric import MetricCreate, MetricOut
from app.services import metric_service, versioning

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.post("", response_model=MetricOut, status_code=status.HTTP_201_CREATED)
def create_metric(
    body: MetricCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[str, Depends(get_actor)],
) -> MetricOut:
    metric = metric_service.create_metric(db, data=body.model_dump(), actor=actor)
    return MetricOut.model_validate(metric)


@router.post("/{key}/versions", response_model=MetricOut, status_code=status.HTTP_201_CREATED)
def revise_metric(
    key: uuid.UUID,
    body: MetricCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[str, Depends(get_actor)],
) -> MetricOut:
    try:
        metric = metric_service.create_metric(db, data=body.model_dump(), actor=actor, key=key)
    except versioning.EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return MetricOut.model_validate(metric)


@router.get("", response_model=list[MetricOut])
def list_metrics(db: Annotated[Session, Depends(get_db)]) -> list[MetricOut]:
    return [MetricOut.model_validate(m) for m in metric_service.list_metrics(db)]


@router.get("/{key}", response_model=MetricOut)
def get_metric(
    key: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> MetricOut:
    metric = metric_service.get_metric(db, key)
    if metric is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Metric {key} not found")
    return MetricOut.model_validate(metric)


@router.get("/{key}/versions", response_model=list[MetricOut])
def list_metric_versions(
    key: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> list[MetricOut]:
    versions = versioning.list_versions(db, Metric, key)
    return [MetricOut.model_validate(m) for m in versions]
