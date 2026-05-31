"""Observability API: eval schedules, jobs, experiments, and metric trends."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_actor
from app.core.database import get_db
from app.models.eval_schedule import EvalSchedule
from app.models.experiment import Experiment
from app.schemas.observability import (
    EvalJobOut,
    EvalScheduleCreate,
    EvalScheduleOut,
    EvalScheduleStatusUpdate,
    ExperimentCreate,
    ExperimentOut,
    ExperimentUpdate,
    TrendOut,
    TrendPoint,
)
from app.services.experiment_service import (
    ObservabilityError,
    create_experiment,
    get_experiment,
    list_experiments,
    update_experiment,
)
from app.services.schedule_service import (
    create_schedule,
    get_schedule,
    list_jobs,
    list_schedules,
    trigger_schedule,
    update_schedule_status,
)
from app.services.trend_service import get_metric_trend

router = APIRouter(prefix="/observe", tags=["observability"])


# ---------- helpers ----------


def _require_schedule(db: Session, key: uuid.UUID) -> EvalSchedule:
    s = get_schedule(db, key)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Schedule {key} not found")
    return s


def _require_experiment(db: Session, key: uuid.UUID) -> Experiment:
    e = get_experiment(db, key)
    if e is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Experiment {key} not found")
    return e


# ---------- schedules ----------


@router.post("/schedules", response_model=EvalScheduleOut, status_code=status.HTTP_201_CREATED)
def create_schedule_endpoint(
    body: EvalScheduleCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[str, Depends(get_actor)],
) -> EvalScheduleOut:
    s = create_schedule(db, body=body, actor=actor)
    return EvalScheduleOut.model_validate(s)


@router.get("/schedules", response_model=list[EvalScheduleOut])
def list_schedules_endpoint(
    db: Annotated[Session, Depends(get_db)],
    by_status: str | None = None,
) -> list[EvalScheduleOut]:
    return [EvalScheduleOut.model_validate(s) for s in list_schedules(db, status=by_status)]


@router.get("/schedules/{schedule_key}", response_model=EvalScheduleOut)
def get_schedule_endpoint(
    schedule_key: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> EvalScheduleOut:
    return EvalScheduleOut.model_validate(_require_schedule(db, schedule_key))


@router.patch("/schedules/{schedule_key}/status", response_model=EvalScheduleOut)
def update_schedule_status_endpoint(
    schedule_key: uuid.UUID,
    body: EvalScheduleStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[str, Depends(get_actor)],
) -> EvalScheduleOut:
    s = _require_schedule(db, schedule_key)
    try:
        updated = update_schedule_status(db, schedule=s, new_status=body.status, actor=actor)
    except ObservabilityError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return EvalScheduleOut.model_validate(updated)


@router.post("/schedules/{schedule_key}/trigger", response_model=EvalJobOut)
def trigger_schedule_endpoint(
    schedule_key: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[str, Depends(get_actor)],
) -> EvalJobOut:
    s = _require_schedule(db, schedule_key)
    try:
        job = trigger_schedule(db, schedule=s, actor=actor)
    except ObservabilityError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return EvalJobOut.model_validate(job)


@router.get("/schedules/{schedule_key}/jobs", response_model=list[EvalJobOut])
def list_jobs_endpoint(
    schedule_key: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> list[EvalJobOut]:
    _require_schedule(db, schedule_key)
    return [EvalJobOut.model_validate(j) for j in list_jobs(db, schedule_key)]


# ---------- experiments ----------


@router.post("/experiments", response_model=ExperimentOut, status_code=status.HTTP_201_CREATED)
def create_experiment_endpoint(
    body: ExperimentCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[str, Depends(get_actor)],
) -> ExperimentOut:
    e = create_experiment(db, body=body, actor=actor)
    return ExperimentOut.model_validate(e)


@router.get("/experiments", response_model=list[ExperimentOut])
def list_experiments_endpoint(
    db: Annotated[Session, Depends(get_db)],
    by_status: str | None = None,
) -> list[ExperimentOut]:
    return [ExperimentOut.model_validate(e) for e in list_experiments(db, status=by_status)]


@router.get("/experiments/{exp_key}", response_model=ExperimentOut)
def get_experiment_endpoint(
    exp_key: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> ExperimentOut:
    return ExperimentOut.model_validate(_require_experiment(db, exp_key))


@router.patch("/experiments/{exp_key}", response_model=ExperimentOut)
def update_experiment_endpoint(
    exp_key: uuid.UUID,
    body: ExperimentUpdate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[str, Depends(get_actor)],
) -> ExperimentOut:
    try:
        e = update_experiment(db, entity_key=exp_key, body=body, actor=actor)
    except ObservabilityError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ExperimentOut.model_validate(e)


# ---------- trends ----------


@router.get("/trends", response_model=TrendOut)
def get_trends_endpoint(
    db: Annotated[Session, Depends(get_db)],
    dataset_key: uuid.UUID = Query(...),
    metric_kind: str = Query(...),
    limit: int = Query(default=50, ge=1, le=200),
) -> TrendOut:
    points = get_metric_trend(db, dataset_key=dataset_key, metric_kind=metric_kind, limit=limit)
    return TrendOut(
        dataset_key=str(dataset_key),
        metric_kind=metric_kind,
        points=[TrendPoint(**p) for p in points],
    )
