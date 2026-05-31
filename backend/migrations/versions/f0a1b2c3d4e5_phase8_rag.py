"""phase8_rag

Revision ID: f0a1b2c3d4e5
Revises: e7f8a9b0c1d2
Create Date: 2026-05-31 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f0a1b2c3d4e5"
down_revision: str | None = "e7f8a9b0c1d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # rag_corpora (versioned entity — inherits VersionedMixin columns)
    op.create_table(
        "rag_corpora",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entity_key", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("is_latest", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=False),
        sa.Column("embedding_model", sa.String(length=128), nullable=False),
        sa.Column("chunk_size", sa.Integer(), nullable=False),
        sa.Column("chunk_overlap", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rag_corpora")),
        sa.UniqueConstraint("entity_key", "version", name="version_per_entity"),
    )
    with op.batch_alter_table("rag_corpora", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_rag_corpora_entity_key"), ["entity_key"], unique=False)

    # rag_documents (immutable event records)
    op.create_table(
        "rag_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("corpus_key", sa.Uuid(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("doc_source", sa.String(length=512), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rag_documents")),
    )
    with op.batch_alter_table("rag_documents", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_rag_documents_corpus_key"), ["corpus_key"], unique=False
        )

    # rag_evals (immutable event records)
    op.create_table(
        "rag_evals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("corpus_key", sa.Uuid(), nullable=False),
        sa.Column("dataset_key", sa.Uuid(), nullable=False),
        sa.Column("retrieval_method", sa.String(length=128), nullable=False),
        sa.Column("top_k", sa.Integer(), nullable=False),
        sa.Column("query_count", sa.Integer(), nullable=False),
        sa.Column("mean_context_relevance", sa.Float(), nullable=False),
        sa.Column("mean_faithfulness", sa.Float(), nullable=False),
        sa.Column("mean_answer_relevance", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rag_evals")),
    )
    with op.batch_alter_table("rag_evals", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_rag_evals_corpus_key"), ["corpus_key"], unique=False)
        batch_op.create_index(batch_op.f("ix_rag_evals_dataset_key"), ["dataset_key"], unique=False)

    # rag_eval_results (immutable per-query result records)
    op.create_table(
        "rag_eval_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("rag_eval_id", sa.Uuid(), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("retrieved_doc_ids", sa.JSON(), nullable=False),
        sa.Column("retrieved_content", sa.JSON(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("context_relevance_score", sa.Float(), nullable=False),
        sa.Column("faithfulness_score", sa.Float(), nullable=False),
        sa.Column("answer_relevance_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rag_eval_results")),
    )
    with op.batch_alter_table("rag_eval_results", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_rag_eval_results_rag_eval_id"), ["rag_eval_id"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("rag_eval_results", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_rag_eval_results_rag_eval_id"))
    op.drop_table("rag_eval_results")

    with op.batch_alter_table("rag_evals", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_rag_evals_dataset_key"))
        batch_op.drop_index(batch_op.f("ix_rag_evals_corpus_key"))
    op.drop_table("rag_evals")

    with op.batch_alter_table("rag_documents", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_rag_documents_corpus_key"))
    op.drop_table("rag_documents")

    with op.batch_alter_table("rag_corpora", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_rag_corpora_entity_key"))
    op.drop_table("rag_corpora")
