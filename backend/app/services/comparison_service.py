"""Comparison service: compute metric deltas and detect regressions between evaluations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.comparison import Comparison
from app.models.evaluation import Evaluation
from app.services import audit

DEFAULT_THRESHOLD = 0.02  # absolute score drop that triggers regression / improvement flag


class ComparisonError(Exception):
    """Raised when a comparison cannot be created (e.g. mismatched datasets)."""


def _delta_for_metric(
    baseline_agg: dict[str, Any],
    candidate_agg: dict[str, Any],
    threshold: float,
) -> dict[str, Any]:
    b_score: float = float(baseline_agg.get("mean_score", 0.0))
    c_score: float = float(candidate_agg.get("mean_score", 0.0))
    delta = round(c_score - b_score, 4)
    relative_delta = round(delta / b_score, 4) if b_score != 0.0 else 0.0
    return {
        "metric_name": str(baseline_agg.get("metric_name", "")),
        "metric_kind": str(baseline_agg.get("metric_kind", "")),
        "baseline_score": round(b_score, 4),
        "candidate_score": round(c_score, 4),
        "delta": delta,
        "relative_delta": relative_delta,
        "regression": delta < -threshold,
        "improvement": delta > threshold,
        "threshold": threshold,
    }


def compute_comparison(
    db: Session,
    *,
    name: str,
    baseline: Evaluation,
    candidate: Evaluation,
    kind: str,
    threshold_config: dict[str, float],
    notes: str | None,
    actor: str,
) -> Comparison:
    """Compute deltas between two evaluations; persist + audit the result."""
    if str(baseline.dataset_key) != str(candidate.dataset_key):
        raise ComparisonError(
            "Both evaluations must use the same dataset_key for a valid comparison. "
            f"baseline.dataset_key={baseline.dataset_key}, "
            f"candidate.dataset_key={candidate.dataset_key}"
        )

    baseline_scores: dict[str, Any] = baseline.aggregate_scores
    candidate_scores: dict[str, Any] = candidate.aggregate_scores
    common_keys = sorted(set(baseline_scores) & set(candidate_scores))

    metric_deltas: dict[str, Any] = {}
    regressions = 0
    improvements = 0

    for mkey in common_keys:
        threshold = threshold_config.get(mkey, DEFAULT_THRESHOLD)
        info = _delta_for_metric(baseline_scores[mkey], candidate_scores[mkey], threshold)
        metric_deltas[mkey] = info
        if info["regression"]:
            regressions += 1
        if info["improvement"]:
            improvements += 1

    if regressions > 0:
        overall_status = "regression"
    elif improvements > 0:
        overall_status = "improvement"
    else:
        overall_status = "neutral"

    now = datetime.now(UTC)
    comparison = Comparison(
        id=uuid.uuid4(),
        name=name,
        created_at=now,
        created_by=actor,
        baseline_id=baseline.id,
        candidate_id=candidate.id,
        kind=kind,
        dataset_key=baseline.dataset_key,
        metric_deltas=metric_deltas,
        threshold_config=threshold_config,
        regressions_detected=regressions,
        improvements_detected=improvements,
        status=overall_status,
        notes=notes,
    )
    db.add(comparison)
    db.flush()

    audit.record_event(
        db,
        actor=actor,
        action="create",
        entity_type="comparisons",
        entity_key=comparison.id,
        entity_version_id=None,
        payload={
            "name": name,
            "kind": kind,
            "baseline_id": str(baseline.id),
            "candidate_id": str(candidate.id),
            "dataset_key": str(baseline.dataset_key),
            "regressions_detected": regressions,
            "improvements_detected": improvements,
            "status": overall_status,
        },
    )
    db.commit()
    db.refresh(comparison)
    return comparison
