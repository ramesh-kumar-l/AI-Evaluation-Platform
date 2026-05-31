"""Evaluation service: in-process orchestration of dataset-level evaluation.

Executes one inference run per dataset item, scores each output with every requested
metric, persists EvaluationResult rows, computes aggregate stats, and records an audit event.
No Temporal cluster required — fully offline.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.evaluation import Evaluation
from app.models.evaluation_result import EvaluationResult
from app.models.metric import Metric
from app.models.prompt import Prompt
from app.models.provider import Model, Provider
from app.services import audit
from app.services.metrics.base import MetricInput
from app.services.metrics.registry import get_scorer
from app.services.run_service import RunError, execute_run


class EvaluationError(Exception):
    """Raised when the evaluation cannot start (e.g. empty dataset, bad config)."""


def _compute_aggregates(
    metric_rows: list[Metric], results: list[EvaluationResult]
) -> dict[str, Any]:
    aggregates: dict[str, Any] = {}
    for metric in metric_rows:
        key = str(metric.entity_key)
        scored = [r for r in results if str(r.metric_key) == key and r.status == "scored"]
        if not scored:
            aggregates[key] = {
                "metric_name": metric.name,
                "metric_kind": metric.kind,
                "mean_score": 0.0,
                "count": 0,
                "confidence_distribution": {},
            }
            continue
        scores = [r.score for r in scored]
        conf_dist: dict[str, int] = {}
        for r in scored:
            conf_dist[r.confidence] = conf_dist.get(r.confidence, 0) + 1
        aggregates[key] = {
            "metric_name": metric.name,
            "metric_kind": metric.kind,
            "mean_score": round(sum(scores) / len(scores), 4),
            "count": len(scored),
            "confidence_distribution": conf_dist,
        }
    return aggregates


def execute_evaluation(
    db: Session,
    *,
    name: str,
    prompt: Prompt,
    model: Model,
    provider: Provider,
    dataset: Dataset,
    metric_rows: list[Metric],
    parameters: dict[str, Any],
    actor: str,
) -> Evaluation:
    """Run a dataset-level evaluation; persist all results + one Evaluation event record."""
    items: list[Any] = dataset.items
    if not items:
        raise EvaluationError("Dataset has no items")

    started_at = datetime.now(UTC)
    result_staging: list[EvaluationResult] = []
    run_ids: list[uuid.UUID] = []
    item_errors: list[str] = []

    for idx, item in enumerate(items):
        input_vars: dict[str, Any] = item.get("input", {}) if isinstance(item, dict) else {}
        expected: str = str(item.get("expected", "")) if isinstance(item, dict) else ""

        try:
            run = execute_run(
                db,
                prompt=prompt,
                model=model,
                provider=provider,
                input_variables=input_vars,
                parameters=parameters,
                actor=actor,
            )
        except RunError as exc:
            item_errors.append(f"item[{idx}] run error: {exc}")
            continue

        run_ids.append(run.id)
        actual = run.raw_output

        for metric in metric_rows:
            scorer = get_scorer(metric.kind)
            try:
                ms = scorer.score(
                    MetricInput(expected=expected, actual=actual, config=metric.config)
                )
                result = EvaluationResult(
                    id=uuid.uuid4(),
                    evaluation_id=uuid.UUID(int=0),  # placeholder; set after Evaluation flush
                    run_id=run.id,
                    item_index=idx,
                    expected_output=expected,
                    metric_key=metric.entity_key,
                    metric_version_id=metric.id,
                    metric_kind=metric.kind,
                    score=ms.score,
                    confidence=ms.confidence,
                    detail=ms.detail,
                    status="scored",
                    error=None,
                )
            except Exception as exc:  # noqa: BLE001
                result = EvaluationResult(
                    id=uuid.uuid4(),
                    evaluation_id=uuid.UUID(int=0),
                    run_id=run.id,
                    item_index=idx,
                    expected_output=expected,
                    metric_key=metric.entity_key,
                    metric_version_id=metric.id,
                    metric_kind=metric.kind,
                    score=0.0,
                    confidence="low",
                    detail={},
                    status="failed",
                    error=str(exc),
                )
            result_staging.append(result)

    scored_items = len(run_ids)
    total_items = len(items)
    if scored_items == total_items:
        status = "completed"
    elif scored_items > 0:
        status = "partial"
    else:
        status = "failed"
    completed_at = datetime.now(UTC)

    aggregate_scores = _compute_aggregates(metric_rows, result_staging)

    evaluation = Evaluation(
        id=uuid.uuid4(),
        name=name,
        created_at=started_at,
        created_by=actor,
        prompt_key=prompt.entity_key,
        model_key=model.entity_key,
        provider_key=provider.entity_key,
        dataset_key=dataset.entity_key,
        prompt_version_id=prompt.id,
        model_version_id=model.id,
        provider_version_id=provider.id,
        dataset_version_id=dataset.id,
        metric_keys=[str(m.entity_key) for m in metric_rows],
        metric_version_ids=[str(m.id) for m in metric_rows],
        parameters=parameters,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        total_items=total_items,
        scored_items=scored_items,
        error="; ".join(item_errors) if item_errors else None,
        aggregate_scores=aggregate_scores,
    )
    db.add(evaluation)
    db.flush()  # obtain evaluation.id before linking results

    for result in result_staging:
        result.evaluation_id = evaluation.id
        db.add(result)

    audit.record_event(
        db,
        actor=actor,
        action="create",
        entity_type="evaluations",
        entity_key=evaluation.id,
        entity_version_id=None,
        payload={
            "name": name,
            "status": status,
            "total_items": total_items,
            "scored_items": scored_items,
            "dataset_key": str(dataset.entity_key),
            "model_key": str(model.entity_key),
        },
    )
    db.commit()
    db.refresh(evaluation)
    return evaluation
