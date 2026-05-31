"""Experiment service: CRUD for A/B experiment groups."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.experiment import Experiment
from app.schemas.observability import ExperimentCreate, ExperimentUpdate
from app.services.versioning import create_version, get_latest, list_latest


class ObservabilityError(Exception):
    """Raised on invalid observability operations."""


def create_experiment(db: Session, *, body: ExperimentCreate, actor: str) -> Experiment:
    return create_version(
        db,
        Experiment,
        fields={
            "name": body.name,
            "description": body.description,
            "evaluation_ids": body.evaluation_ids,
            "status": "active",
            "hypothesis": body.hypothesis,
            "conclusion": "",
        },
        actor=actor,
        audit_payload={"name": body.name, "hypothesis": body.hypothesis},
    )


def update_experiment(
    db: Session, *, entity_key: uuid.UUID, body: ExperimentUpdate, actor: str
) -> Experiment:
    existing = get_latest(db, Experiment, entity_key)
    if existing is None:
        raise ObservabilityError(f"Experiment {entity_key} not found")

    updated: dict[str, Any] = {
        "name": existing.name,
        "description": existing.description,
        "evaluation_ids": body.evaluation_ids
        if body.evaluation_ids is not None
        else existing.evaluation_ids,
        "status": body.status if body.status is not None else existing.status,
        "hypothesis": existing.hypothesis,
        "conclusion": body.conclusion if body.conclusion is not None else existing.conclusion,
    }
    return create_version(
        db,
        Experiment,
        fields=updated,
        actor=actor,
        entity_key=entity_key,
        audit_payload={k: v for k, v in updated.items() if k in ("status", "conclusion")},
    )


def get_experiment(db: Session, entity_key: uuid.UUID) -> Experiment | None:
    return get_latest(db, Experiment, entity_key)


def list_experiments(db: Session, *, status: str | None = None) -> list[Experiment]:
    results = list_latest(db, Experiment)
    if status is not None:
        results = [e for e in results if e.status == status]
    return results
