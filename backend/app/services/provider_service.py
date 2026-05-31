"""Provider and Model service: create/revise versioned records."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.provider import Model, Provider
from app.services import versioning


def create_provider(
    db: Session, *, data: dict[str, Any], actor: str, key: uuid.UUID | None = None
) -> Provider:
    return versioning.create_version(db, Provider, fields=data, actor=actor, entity_key=key)


def create_model(
    db: Session, *, data: dict[str, Any], actor: str, key: uuid.UUID | None = None
) -> Model:
    return versioning.create_version(db, Model, fields=data, actor=actor, entity_key=key)
