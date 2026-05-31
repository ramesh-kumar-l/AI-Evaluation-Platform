"""Comparisons API: create and retrieve pairwise evaluation comparisons."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_actor
from app.core.database import get_db
from app.models.comparison import Comparison
from app.models.evaluation import Evaluation
from app.schemas.comparison import ComparisonCreate, ComparisonOut
from app.services.comparison_service import ComparisonError, compute_comparison

router = APIRouter(prefix="/comparisons", tags=["comparisons"])


def _get_evaluation(db: Session, eid: uuid.UUID) -> Evaluation:
    ev = db.get(Evaluation, eid)
    if ev is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Evaluation {eid} not found")
    return ev


@router.post("", response_model=ComparisonOut, status_code=status.HTTP_201_CREATED)
def create_comparison(
    body: ComparisonCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[str, Depends(get_actor)],
) -> ComparisonOut:
    baseline = _get_evaluation(db, body.baseline_id)
    candidate = _get_evaluation(db, body.candidate_id)
    try:
        comp = compute_comparison(
            db,
            name=body.name,
            baseline=baseline,
            candidate=candidate,
            kind=body.kind,
            threshold_config=body.threshold_config,
            notes=body.notes,
            actor=actor,
        )
    except ComparisonError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return ComparisonOut.model_validate(comp)


@router.get("", response_model=list[ComparisonOut])
def list_comparisons(
    db: Annotated[Session, Depends(get_db)],
    baseline_id: Annotated[uuid.UUID | None, Query()] = None,
    candidate_id: Annotated[uuid.UUID | None, Query()] = None,
    dataset_key: Annotated[uuid.UUID | None, Query()] = None,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[ComparisonOut]:
    stmt = select(Comparison).order_by(Comparison.created_at.desc()).limit(limit)
    if baseline_id is not None:
        stmt = stmt.where(Comparison.baseline_id == baseline_id)
    if candidate_id is not None:
        stmt = stmt.where(Comparison.candidate_id == candidate_id)
    if dataset_key is not None:
        stmt = stmt.where(Comparison.dataset_key == dataset_key)
    if status_filter is not None:
        stmt = stmt.where(Comparison.status == status_filter)
    rows = list(db.execute(stmt).scalars().all())
    return [ComparisonOut.model_validate(r) for r in rows]


@router.get("/{comparison_id}", response_model=ComparisonOut)
def get_comparison(
    comparison_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> ComparisonOut:
    comp = db.get(Comparison, comparison_id)
    if comp is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"Comparison {comparison_id} not found"
        )
    return ComparisonOut.model_validate(comp)
