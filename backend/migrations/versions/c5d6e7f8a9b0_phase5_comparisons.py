"""phase5_comparisons

Revision ID: c5d6e7f8a9b0
Revises: a8a557afd538
Create Date: 2026-05-31 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c5d6e7f8a9b0"
down_revision: str | None = "a8a557afd538"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "comparisons",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("baseline_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("dataset_key", sa.Uuid(), nullable=False),
        sa.Column("metric_deltas", sa.JSON(), nullable=False),
        sa.Column("threshold_config", sa.JSON(), nullable=False),
        sa.Column("regressions_detected", sa.Integer(), nullable=False),
        sa.Column("improvements_detected", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_comparisons")),
    )
    with op.batch_alter_table("comparisons", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_comparisons_baseline_id"), ["baseline_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_comparisons_candidate_id"), ["candidate_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_comparisons_dataset_key"), ["dataset_key"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("comparisons", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_comparisons_dataset_key"))
        batch_op.drop_index(batch_op.f("ix_comparisons_candidate_id"))
        batch_op.drop_index(batch_op.f("ix_comparisons_baseline_id"))

    op.drop_table("comparisons")
