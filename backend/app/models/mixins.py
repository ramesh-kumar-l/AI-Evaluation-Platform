"""Reusable column mixins: immutable versioning + lineage, and timestamps.

Any entity that mixes in ``VersionedMixin`` becomes immutable and versioned: a change is a new row
with an incremented ``version``, a ``parent_id`` lineage pointer to its predecessor, and an
``is_latest`` flag. See ADR-0002.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.models.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class VersionedMixin:
    """Immutable-versioning columns shared by all versioned domain entities."""

    # This row's unique id (one row == one immutable version).
    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)

    # Stable logical identity shared across all versions of the same entity.
    entity_key: Mapped[uuid.UUID] = mapped_column(Uuid(), index=True, nullable=False)

    # 1-based version number, unique within an entity_key.
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    # Lineage pointer to the predecessor version's id (None for v1). Not a hard FK so the mixin
    # stays table-agnostic; integrity is enforced by the versioning service.
    parent_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)

    # Convenience flag: exactly one row per entity_key has is_latest=True.
    is_latest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="system")

    @declared_attr.directive
    def __table_args__(cls) -> tuple[object, ...]:  # noqa: N805
        return (UniqueConstraint("entity_key", "version", name="version_per_entity"),)


class VersionedBase(VersionedMixin, Base):
    """Abstract mapped base for all versioned entities.

    Concrete entities subclass this (not the mixin directly) so the generic versioning service has a
    single, fully typed base to operate on.
    """

    __abstract__ = True
    # Set by each concrete subclass; declared here for the type checker.
    __tablename__: str
