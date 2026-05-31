"""Benchmark service: create benchmarks and manage lifecycle transitions."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.benchmark import Benchmark
from app.services.versioning import create_version, get_latest, list_latest

# Strictly unidirectional lifecycle DAG. Keys = target status, values = allowed current statuses.
_VALID_TRANSITIONS: dict[str, set[str]] = {
    "active": {"draft"},
    "deprecated": {"draft", "active"},
    "archived": {"deprecated"},
}


class BenchmarkError(Exception):
    """Raised when a benchmark lifecycle operation is invalid."""


def create_benchmark(
    db: Session,
    *,
    name: str,
    description: str,
    domain: str,
    task_type: str,
    metric_keys: list[Any],
    dataset_key: uuid.UUID | None,
    notes: str | None,
    actor: str,
) -> Benchmark:
    return create_version(
        db,
        Benchmark,
        fields={
            "name": name,
            "description": description,
            "domain": domain,
            "task_type": task_type,
            "metric_keys": metric_keys,
            "dataset_key": dataset_key,
            "status": "draft",
            "notes": notes,
        },
        actor=actor,
        audit_payload={"name": name, "domain": domain, "task_type": task_type},
    )


def get_benchmark(db: Session, benchmark_key: uuid.UUID) -> Benchmark | None:
    return get_latest(db, Benchmark, benchmark_key)


def list_benchmarks(db: Session, *, status_filter: str | None = None) -> list[Benchmark]:
    results = list_latest(db, Benchmark)
    if status_filter is not None:
        results = [b for b in results if b.status == status_filter]
    return results


def set_benchmark_status(
    db: Session,
    *,
    benchmark: Benchmark,
    new_status: str,
    notes: str | None,
    actor: str,
) -> Benchmark:
    """Transition benchmark lifecycle; creates a new immutable version."""
    allowed_from = _VALID_TRANSITIONS.get(new_status, set())
    if benchmark.status not in allowed_from:
        raise BenchmarkError(
            f"Cannot transition from '{benchmark.status}' to '{new_status}'. "
            f"Allowed source statuses: {sorted(allowed_from) or 'none'}"
        )
    return create_version(
        db,
        Benchmark,
        fields={
            "name": benchmark.name,
            "description": benchmark.description,
            "domain": benchmark.domain,
            "task_type": benchmark.task_type,
            "metric_keys": benchmark.metric_keys,
            "dataset_key": benchmark.dataset_key,
            "status": new_status,
            "notes": notes if notes is not None else benchmark.notes,
        },
        actor=actor,
        entity_key=benchmark.entity_key,
        audit_payload={"previous_status": benchmark.status, "new_status": new_status},
    )
