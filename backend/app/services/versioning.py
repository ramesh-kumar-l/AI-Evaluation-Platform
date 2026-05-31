"""Generic immutable-versioning service shared by all versioned entities. See ADR-0002.

A change never updates a row in place: it inserts a new version, repoints lineage, flips the prior
``is_latest`` flag, and records an audit event — all in one transaction-flush.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.mixins import VersionedBase
from app.services import audit


class EntityNotFoundError(Exception):
    """Raised when revising or reading an entity_key that has no current version."""


def get_latest[T: VersionedBase](
    db: Session, model_cls: type[T], entity_key: uuid.UUID
) -> T | None:
    stmt = select(model_cls).where(
        model_cls.entity_key == entity_key, model_cls.is_latest.is_(True)
    )
    return db.execute(stmt).scalar_one_or_none()


def get_version[T: VersionedBase](
    db: Session, model_cls: type[T], entity_key: uuid.UUID, version: int
) -> T | None:
    stmt = select(model_cls).where(model_cls.entity_key == entity_key, model_cls.version == version)
    return db.execute(stmt).scalar_one_or_none()


def list_versions[T: VersionedBase](
    db: Session, model_cls: type[T], entity_key: uuid.UUID
) -> list[T]:
    stmt = select(model_cls).where(model_cls.entity_key == entity_key).order_by(model_cls.version)
    return list(db.execute(stmt).scalars().all())


def list_latest[T: VersionedBase](db: Session, model_cls: type[T]) -> list[T]:
    stmt = select(model_cls).where(model_cls.is_latest.is_(True)).order_by(model_cls.created_at)
    return list(db.execute(stmt).scalars().all())


def create_version[T: VersionedBase](
    db: Session,
    model_cls: type[T],
    *,
    fields: dict[str, Any],
    actor: str,
    entity_key: uuid.UUID | None = None,
    audit_payload: dict[str, Any] | None = None,
) -> T:
    """Create v1 (when ``entity_key`` is None) or the next version of an existing entity.

    Commits the transaction so the new version and its audit event persist atomically.
    """
    if entity_key is None:
        entity_key = uuid.uuid4()
        version, parent_id, action = 1, None, "create"
    else:
        current = get_latest(db, model_cls, entity_key)
        if current is None:
            raise EntityNotFoundError(
                f"{model_cls.__tablename__}:{entity_key} has no current version"
            )
        version, parent_id, action = current.version + 1, current.id, "new_version"
        current.is_latest = False

    instance = model_cls(
        entity_key=entity_key,
        version=version,
        parent_id=parent_id,
        is_latest=True,
        created_by=actor,
        **fields,
    )
    db.add(instance)
    db.flush()

    audit.record_event(
        db,
        actor=actor,
        action=action,
        entity_type=model_cls.__tablename__,
        entity_key=entity_key,
        entity_version_id=instance.id,
        payload=audit_payload if audit_payload is not None else fields,
    )
    db.commit()
    db.refresh(instance)
    return instance
