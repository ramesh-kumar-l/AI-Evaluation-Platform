"""DatasetPolicy service: upsert and retrieve governance policies for datasets."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.dataset_policy import DatasetPolicy
from app.services import audit
from app.services.versioning import get_latest


class PolicyError(Exception):
    """Raised when a policy operation cannot proceed."""


def upsert_policy(
    db: Session,
    *,
    dataset_key: uuid.UUID,
    owner: str,
    status: str,
    quality_rules: dict[str, Any],
    ground_truth_policy: dict[str, Any],
    notes: str | None,
    actor: str,
) -> DatasetPolicy:
    """Create or update the governance policy for a dataset_key."""
    if get_latest(db, Dataset, dataset_key) is None:
        raise PolicyError(f"Dataset {dataset_key} not found")

    stmt = select(DatasetPolicy).where(DatasetPolicy.dataset_key == dataset_key)
    existing = db.execute(stmt).scalar_one_or_none()
    now = datetime.now(UTC)

    if existing is not None:
        existing.owner = owner
        existing.status = status
        existing.quality_rules = quality_rules
        existing.ground_truth_policy = ground_truth_policy
        existing.notes = notes
        existing.updated_at = now
        policy = existing
    else:
        policy = DatasetPolicy(
            id=uuid.uuid4(),
            dataset_key=dataset_key,
            owner=owner,
            status=status,
            quality_rules=quality_rules,
            ground_truth_policy=ground_truth_policy,
            notes=notes,
            created_at=now,
            updated_at=now,
            created_by=actor,
        )
        db.add(policy)

    db.flush()
    audit.record_event(
        db,
        actor=actor,
        action="upsert_policy",
        entity_type="dataset_policies",
        entity_key=dataset_key,
        entity_version_id=policy.id,
        payload={"owner": owner, "status": status},
    )
    db.commit()
    db.refresh(policy)
    return policy


def get_policy(db: Session, dataset_key: uuid.UUID) -> DatasetPolicy | None:
    stmt = select(DatasetPolicy).where(DatasetPolicy.dataset_key == dataset_key)
    return db.execute(stmt).scalar_one_or_none()
