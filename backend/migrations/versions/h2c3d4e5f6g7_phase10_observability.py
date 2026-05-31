"""phase10_observability

Revision ID: h2c3d4e5f6g7
Revises: g1b2c3d4e5f6
Create Date: 2026-05-31 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "h2c3d4e5f6g7"
down_revision: str | None = "g1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # eval_schedules (versioned entity)
    op.create_table(
        "eval_schedules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entity_key", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("is_latest", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("dataset_key", sa.Uuid(), nullable=False),
        sa.Column("model_key", sa.Uuid(), nullable=False),
        sa.Column("prompt_key", sa.Uuid(), nullable=False),
        sa.Column("metric_keys", sa.JSON(), nullable=False),
        sa.Column("cron_expr", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_eval_schedules")),
        sa.UniqueConstraint("entity_key", "version", name="version_per_entity"),
    )
    with op.batch_alter_table("eval_schedules", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_eval_schedules_entity_key"), ["entity_key"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_eval_schedules_status"), ["status"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_eval_schedules_dataset_key"), ["dataset_key"], unique=False
        )

    # eval_jobs (immutable event)
    op.create_table(
        "eval_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("schedule_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("eval_id", sa.Uuid(), nullable=True),
        sa.Column("error_msg", sa.Text(), nullable=False),
        sa.Column("triggered_by", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_eval_jobs")),
    )
    with op.batch_alter_table("eval_jobs", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_eval_jobs_schedule_id"), ["schedule_id"], unique=False
        )

    # experiments (versioned entity)
    op.create_table(
        "experiments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entity_key", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("is_latest", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evaluation_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("conclusion", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_experiments")),
        sa.UniqueConstraint("entity_key", "version", name="version_per_entity"),
    )
    with op.batch_alter_table("experiments", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_experiments_entity_key"), ["entity_key"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_experiments_status"), ["status"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("experiments", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_experiments_status"))
        batch_op.drop_index(batch_op.f("ix_experiments_entity_key"))
    op.drop_table("experiments")

    with op.batch_alter_table("eval_jobs", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_eval_jobs_schedule_id"))
    op.drop_table("eval_jobs")

    with op.batch_alter_table("eval_schedules", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_eval_schedules_dataset_key"))
        batch_op.drop_index(batch_op.f("ix_eval_schedules_status"))
        batch_op.drop_index(batch_op.f("ix_eval_schedules_entity_key"))
    op.drop_table("eval_schedules")
