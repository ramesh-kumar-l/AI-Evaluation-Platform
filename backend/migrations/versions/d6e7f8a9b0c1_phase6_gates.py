"""phase6_gates

Revision ID: d6e7f8a9b0c1
Revises: c5d6e7f8a9b0
Create Date: 2026-05-31 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d6e7f8a9b0c1"
down_revision: str | None = "c5d6e7f8a9b0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # release_gates (versioned)
    op.create_table(
        "release_gates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entity_key", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("is_latest", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=False),
        sa.Column("criteria", sa.JSON(), nullable=False),
        sa.Column("max_regressions_allowed", sa.Integer(), nullable=False),
        sa.Column("require_approval", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_release_gates")),
        sa.UniqueConstraint("entity_key", "version", name="version_per_entity"),
    )
    with op.batch_alter_table("release_gates", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_release_gates_entity_key"), ["entity_key"], unique=False
        )

    # gate_decisions (immutable event records)
    op.create_table(
        "gate_decisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("gate_key", sa.Uuid(), nullable=False),
        sa.Column("gate_version_id", sa.Uuid(), nullable=False),
        sa.Column("comparison_id", sa.Uuid(), nullable=False),
        sa.Column("criteria_results", sa.JSON(), nullable=False),
        sa.Column("criteria_passed", sa.Integer(), nullable=False),
        sa.Column("criteria_failed", sa.Integer(), nullable=False),
        sa.Column("regressions_detected", sa.Integer(), nullable=False),
        sa.Column("max_regressions_allowed", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("override", sa.Boolean(), nullable=False),
        sa.Column("override_justification", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_gate_decisions")),
    )
    with op.batch_alter_table("gate_decisions", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_gate_decisions_gate_key"), ["gate_key"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_gate_decisions_comparison_id"), ["comparison_id"], unique=False
        )

    # approvals (immutable event records)
    op.create_table(
        "approvals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("decision_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_approvals")),
    )
    with op.batch_alter_table("approvals", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_approvals_decision_id"), ["decision_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("approvals", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_approvals_decision_id"))
    op.drop_table("approvals")

    with op.batch_alter_table("gate_decisions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_gate_decisions_comparison_id"))
        batch_op.drop_index(batch_op.f("ix_gate_decisions_gate_key"))
    op.drop_table("gate_decisions")

    with op.batch_alter_table("release_gates", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_release_gates_entity_key"))
    op.drop_table("release_gates")
