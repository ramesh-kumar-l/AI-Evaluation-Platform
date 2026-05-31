"""DatasetPolicy — governance rules for a dataset lineage.

One policy record per dataset_key (upsert semantics). Tracks quality rules,
ground-truth policy, lifecycle status, and ownership for a dataset lineage.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class DatasetPolicy(Base):
    __tablename__ = "dataset_policies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    dataset_key: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False, default="system")
    # Lifecycle: active (default) | deprecated | archived
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    quality_rules: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    ground_truth_policy: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="system")
