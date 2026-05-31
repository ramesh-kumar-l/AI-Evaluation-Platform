"""Schedule service: CRUD for EvalSchedule + trigger to run evaluations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.eval_job import EvalJob
from app.models.eval_schedule import EvalSchedule
from app.models.metric import Metric
from app.models.prompt import Prompt
from app.models.provider import Model, Provider
from app.services.evaluation_service import execute_evaluation
from app.services.experiment_service import ObservabilityError
from app.services.versioning import (
    create_version,
    get_latest,
    list_latest,
)

# Schedule status transitions: key = target, value = allowed source statuses.
_SCHEDULE_TRANSITIONS: dict[str, set[str]] = {
    "active": {"paused"},
    "paused": {"active"},
    "archived": {"paused"},  # must pause before archiving
}


def create_schedule(db: Session, *, body: Any, actor: str) -> EvalSchedule:
    from app.schemas.observability import EvalScheduleCreate

    b: EvalScheduleCreate = body
    return create_version(
        db,
        EvalSchedule,
        fields={
            "name": b.name,
            "description": b.description,
            "dataset_key": b.dataset_key,
            "model_key": b.model_key,
            "prompt_key": b.prompt_key,
            "metric_keys": b.metric_keys,
            "cron_expr": b.cron_expr,
            "status": "active",
            "last_run_at": None,
            "next_run_at": None,
        },
        actor=actor,
        audit_payload={"name": b.name, "cron_expr": b.cron_expr},
    )


def update_schedule_status(
    db: Session,
    *,
    schedule: EvalSchedule,
    new_status: str,
    actor: str,
) -> EvalSchedule:
    allowed = _SCHEDULE_TRANSITIONS.get(new_status, set())
    if schedule.status not in allowed:
        raise ObservabilityError(
            f"Cannot transition schedule from '{schedule.status}' to '{new_status}'. "
            f"Allowed sources: {sorted(allowed) or 'none'}"
        )
    fields: dict[str, Any] = {
        "name": schedule.name,
        "description": schedule.description,
        "dataset_key": schedule.dataset_key,
        "model_key": schedule.model_key,
        "prompt_key": schedule.prompt_key,
        "metric_keys": schedule.metric_keys,
        "cron_expr": schedule.cron_expr,
        "status": new_status,
        "last_run_at": schedule.last_run_at,
        "next_run_at": schedule.next_run_at,
    }
    return create_version(
        db,
        EvalSchedule,
        fields=fields,
        actor=actor,
        entity_key=schedule.entity_key,
        audit_payload={"previous_status": schedule.status, "new_status": new_status},
    )


def get_schedule(db: Session, entity_key: uuid.UUID) -> EvalSchedule | None:
    return get_latest(db, EvalSchedule, entity_key)


def list_schedules(db: Session, *, status: str | None = None) -> list[EvalSchedule]:
    results = list_latest(db, EvalSchedule)
    if status is not None:
        results = [s for s in results if s.status == status]
    return results


def list_jobs(db: Session, schedule_entity_key: uuid.UUID) -> list[EvalJob]:
    stmt = (
        select(EvalJob)
        .where(EvalJob.schedule_id == schedule_entity_key)
        .order_by(EvalJob.started_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def trigger_schedule(
    db: Session,
    *,
    schedule: EvalSchedule,
    actor: str,
) -> EvalJob:
    """Run an on-demand evaluation for this schedule; return the EvalJob record."""
    if schedule.status == "archived":
        raise ObservabilityError("Cannot trigger an archived schedule")

    # Validate all resources exist before creating the job.
    from app.models.dataset import Dataset
    from app.services.versioning import get_latest as _gl

    dataset = _gl(db, Dataset, schedule.dataset_key)
    if dataset is None:
        raise ObservabilityError(f"Dataset {schedule.dataset_key} not found")
    model = _gl(db, Model, schedule.model_key)
    if model is None:
        raise ObservabilityError(f"Model {schedule.model_key} not found")
    provider = _gl(db, Provider, model.provider_key)
    if provider is None:
        raise ObservabilityError("Provider for model not found")
    prompt = _gl(db, Prompt, schedule.prompt_key)
    if prompt is None:
        raise ObservabilityError(f"Prompt {schedule.prompt_key} not found")
    metric_rows = [
        _gl(db, Metric, uuid.UUID(k)) for k in (schedule.metric_keys or [])
    ]
    metric_rows_clean = [m for m in metric_rows if m is not None]

    now = datetime.now(UTC)
    job = EvalJob(
        id=uuid.uuid4(),
        schedule_id=schedule.entity_key,
        status="running",
        eval_id=None,
        error_msg="",
        triggered_by="manual",
        started_at=now,
        completed_at=None,
    )
    db.add(job)
    db.commit()
    job_id = job.id

    try:
        eval_obj = execute_evaluation(
            db,
            name=f"scheduled:{schedule.name}",
            prompt=prompt,
            model=model,
            provider=provider,
            dataset=dataset,
            metric_rows=metric_rows_clean,
            parameters={},
            actor=actor,
        )
        j = db.get(EvalJob, job_id)
        assert j is not None
        j.status = "completed"
        j.eval_id = eval_obj.id
        j.completed_at = datetime.now(UTC)
        db.commit()
    except Exception as exc:
        db.rollback()
        j = db.get(EvalJob, job_id)
        if j is not None:
            j.status = "failed"
            j.error_msg = str(exc)[:500]
            j.completed_at = datetime.now(UTC)
            db.commit()

    result = db.get(EvalJob, job_id)
    assert result is not None
    return result
