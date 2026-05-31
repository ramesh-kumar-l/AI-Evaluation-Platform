"""Benchmarks API: create, list, get, and manage benchmark lifecycle."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_actor
from app.core.database import get_db
from app.models.benchmark import Benchmark
from app.schemas.benchmark import BenchmarkCreate, BenchmarkOut, BenchmarkStatusUpdate
from app.services.benchmark_service import (
    BenchmarkError,
    create_benchmark,
    get_benchmark,
    list_benchmarks,
    set_benchmark_status,
)

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])


def _require_benchmark(db: Session, benchmark_key: uuid.UUID) -> Benchmark:
    b = get_benchmark(db, benchmark_key)
    if b is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"Benchmark {benchmark_key} not found"
        )
    return b


@router.post("", response_model=BenchmarkOut, status_code=status.HTTP_201_CREATED)
def create_benchmark_endpoint(
    body: BenchmarkCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[str, Depends(get_actor)],
) -> BenchmarkOut:
    b = create_benchmark(
        db,
        name=body.name,
        description=body.description,
        domain=body.domain,
        task_type=body.task_type,
        metric_keys=body.metric_keys,
        dataset_key=body.dataset_key,
        notes=body.notes,
        actor=actor,
    )
    return BenchmarkOut.model_validate(b)


@router.get("", response_model=list[BenchmarkOut])
def list_benchmarks_endpoint(
    db: Annotated[Session, Depends(get_db)],
    by_status: str | None = None,
) -> list[BenchmarkOut]:
    return [BenchmarkOut.model_validate(b) for b in list_benchmarks(db, status_filter=by_status)]


@router.get("/{benchmark_key}", response_model=BenchmarkOut)
def get_benchmark_endpoint(
    benchmark_key: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> BenchmarkOut:
    return BenchmarkOut.model_validate(_require_benchmark(db, benchmark_key))


@router.patch(
    "/{benchmark_key}/status",
    response_model=BenchmarkOut,
)
def update_benchmark_status(
    benchmark_key: uuid.UUID,
    body: BenchmarkStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[str, Depends(get_actor)],
) -> BenchmarkOut:
    b = _require_benchmark(db, benchmark_key)
    try:
        updated = set_benchmark_status(
            db, benchmark=b, new_status=body.status, notes=body.notes, actor=actor
        )
    except BenchmarkError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return BenchmarkOut.model_validate(updated)
