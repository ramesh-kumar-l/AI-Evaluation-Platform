"""phase7_benchmarks

Revision ID: e7f8a9b0c1d2
Revises: d6e7f8a9b0c1
Create Date: 2026-05-31 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e7f8a9b0c1d2"
down_revision: str | None = "d6e7f8a9b0c1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # benchmarks (versioned entity — inherits VersionedMixin columns)
    op.create_table(
        "benchmarks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entity_key", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("is_latest", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("task_type", sa.String(length=255), nullable=False),
        sa.Column("metric_keys", sa.JSON(), nullable=False),
        sa.Column("dataset_key", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_benchmarks")),
        sa.UniqueConstraint("entity_key", "version", name="version_per_entity"),
    )
    with op.batch_alter_table("benchmarks", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_benchmarks_entity_key"), ["entity_key"], unique=False)
        batch_op.create_index(batch_op.f("ix_benchmarks_status"), ["status"], unique=False)

    # dataset_policies (mutable governance record — one per dataset_key)
    op.create_table(
        "dataset_policies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("dataset_key", sa.Uuid(), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("quality_rules", sa.JSON(), nullable=False),
        sa.Column("ground_truth_policy", sa.JSON(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dataset_policies")),
    )
    with op.batch_alter_table("dataset_policies", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_dataset_policies_dataset_key"), ["dataset_key"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("dataset_policies", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_dataset_policies_dataset_key"))
    op.drop_table("dataset_policies")

    with op.batch_alter_table("benchmarks", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_benchmarks_status"))
        batch_op.drop_index(batch_op.f("ix_benchmarks_entity_key"))
    op.drop_table("benchmarks")
