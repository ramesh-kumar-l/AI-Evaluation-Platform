"""Metric CRUD service: thin wrapper over the generic versioning service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.metric import Metric
from app.services import versioning


def create_metric(
    db: Session,
    *,
    data: dict[str, Any],
    actor: str,
    key: uuid.UUID | None = None,
) -> Metric:
    """Create v1 of a new metric, or a new version of an existing one."""
    return versioning.create_version(
        db,
        Metric,
        fields=data,
        actor=actor,
        entity_key=key,
    )


def get_metric(db: Session, entity_key: uuid.UUID) -> Metric | None:
    return versioning.get_latest(db, Metric, entity_key)


def list_metrics(db: Session) -> list[Metric]:
    return versioning.list_latest(db, Metric)
