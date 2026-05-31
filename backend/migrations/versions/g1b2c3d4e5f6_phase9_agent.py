"""phase9_agent

Revision ID: g1b2c3d4e5f6
Revises: f0a1b2c3d4e5
Create Date: 2026-05-31 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "g1b2c3d4e5f6"
down_revision = "f0a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("agent_name", sa.String(255), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("final_answer", sa.Text(), nullable=False),
        sa.Column("tool_calls", sa.JSON(), nullable=False),
        sa.Column("step_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_runs_agent_name", "agent_runs", ["agent_name"])

    op.create_table(
        "agent_steps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("agent_run_id", sa.Uuid(), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("step_type", sa.String(32), nullable=False),
        sa.Column("tool_name", sa.String(255), nullable=False),
        sa.Column("tool_input", sa.JSON(), nullable=False),
        sa.Column("tool_output", sa.Text(), nullable=False),
        sa.Column("reasoning_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_steps_agent_run_id", "agent_steps", ["agent_run_id"])

    op.create_table(
        "agent_evals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("dataset_key", sa.Uuid(), nullable=False),
        sa.Column("agent_name", sa.String(255), nullable=False),
        sa.Column("query_count", sa.Integer(), nullable=False),
        sa.Column("mean_tool_accuracy", sa.Float(), nullable=False),
        sa.Column("mean_trajectory_score", sa.Float(), nullable=False),
        sa.Column("mean_task_completion", sa.Float(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_evals_dataset_key", "agent_evals", ["dataset_key"])
    op.create_index("ix_agent_evals_agent_name", "agent_evals", ["agent_name"])

    op.create_table(
        "agent_eval_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("agent_eval_id", sa.Uuid(), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("expected_answer", sa.Text(), nullable=False),
        sa.Column("actual_answer", sa.Text(), nullable=False),
        sa.Column("expected_tools", sa.JSON(), nullable=False),
        sa.Column("actual_tools", sa.JSON(), nullable=False),
        sa.Column("tool_call_accuracy", sa.Float(), nullable=False),
        sa.Column("trajectory_score", sa.Float(), nullable=False),
        sa.Column("task_completion_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_agent_eval_results_agent_eval_id",
        "agent_eval_results",
        ["agent_eval_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_agent_eval_results_agent_eval_id", table_name="agent_eval_results")
    op.drop_table("agent_eval_results")
    op.drop_index("ix_agent_evals_agent_name", table_name="agent_evals")
    op.drop_index("ix_agent_evals_dataset_key", table_name="agent_evals")
    op.drop_table("agent_evals")
    op.drop_index("ix_agent_steps_agent_run_id", table_name="agent_steps")
    op.drop_table("agent_steps")
    op.drop_index("ix_agent_runs_agent_name", table_name="agent_runs")
    op.drop_table("agent_runs")
