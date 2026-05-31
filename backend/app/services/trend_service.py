"""Trend service: query metric quality trends from historical evaluations."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evaluation import Evaluation


def get_metric_trend(
    db: Session,
    *,
    dataset_key: uuid.UUID,
    metric_kind: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return mean_score per evaluation for a dataset_key + metric_kind, oldest first.

    Derives trend data from existing Evaluation.aggregate_scores — no separate model needed.
    """
    stmt = (
        select(Evaluation)
        .where(Evaluation.dataset_key == dataset_key)
        .order_by(Evaluation.created_at.asc())
        .limit(limit)
    )
    evals = list(db.execute(stmt).scalars().all())

    points: list[dict[str, Any]] = []
    for ev in evals:
        scores: dict[str, Any] = ev.aggregate_scores or {}
        for val in scores.values():
            if isinstance(val, dict) and val.get("metric_kind") == metric_kind:
                points.append(
                    {
                        "eval_id": str(ev.id),
                        "created_at": ev.created_at,
                        "mean_score": float(val.get("mean_score", 0.0)),
                        "status": ev.status,
                    }
                )
                break  # one point per eval for this metric_kind
    return points
