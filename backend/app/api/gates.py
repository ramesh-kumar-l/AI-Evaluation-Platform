"""Release Gates API: create gates, evaluate against comparisons, approve/reject decisions."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_actor
from app.core.database import get_db
from app.models.gate_decision import GateDecision
from app.models.release_gate import ReleaseGate
from app.schemas.gate_decision import (
    ApprovalCreate,
    ApprovalOut,
    GateDecisionOut,
    GateEvaluateRequest,
)
from app.schemas.release_gate import ReleaseGateCreate, ReleaseGateOut
from app.services.approval_service import ApprovalError, apply_approval
from app.services.gate_service import (
    GateError,
    create_gate,
    evaluate_gate,
    get_gate,
    list_decisions,
    list_gates,
)

router = APIRouter(prefix="/gates", tags=["gates"])


def _require_gate(db: Session, gate_key: uuid.UUID) -> ReleaseGate:
    gate = get_gate(db, gate_key)
    if gate is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Gate {gate_key} not found")
    return gate


def _require_decision(db: Session, decision_id: uuid.UUID) -> GateDecision:
    decision = db.get(GateDecision, decision_id)
    if decision is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Decision {decision_id} not found")
    return decision


# ---------------------------------------------------------------------------
# Gate CRUD
# ---------------------------------------------------------------------------


@router.post("", response_model=ReleaseGateOut, status_code=status.HTTP_201_CREATED)
def create_release_gate(
    body: ReleaseGateCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[str, Depends(get_actor)],
) -> ReleaseGateOut:
    gate = create_gate(
        db,
        name=body.name,
        description=body.description,
        criteria=[c.model_dump() for c in body.criteria],
        max_regressions_allowed=body.max_regressions_allowed,
        require_approval=body.require_approval,
        notes=body.notes,
        actor=actor,
    )
    return ReleaseGateOut.model_validate(gate)


@router.get("", response_model=list[ReleaseGateOut])
def list_release_gates(
    db: Annotated[Session, Depends(get_db)],
) -> list[ReleaseGateOut]:
    return [ReleaseGateOut.model_validate(g) for g in list_gates(db)]


@router.get("/{gate_key}", response_model=ReleaseGateOut)
def get_release_gate(
    gate_key: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> ReleaseGateOut:
    gate = _require_gate(db, gate_key)
    return ReleaseGateOut.model_validate(gate)


# ---------------------------------------------------------------------------
# Gate evaluation
# ---------------------------------------------------------------------------


@router.post(
    "/{gate_key}/evaluate",
    response_model=GateDecisionOut,
    status_code=status.HTTP_201_CREATED,
)
def evaluate_release_gate(
    gate_key: uuid.UUID,
    body: GateEvaluateRequest,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[str, Depends(get_actor)],
) -> GateDecisionOut:
    gate = _require_gate(db, gate_key)
    try:
        decision = evaluate_gate(db, gate=gate, comparison_id=body.comparison_id, actor=actor)
    except GateError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return GateDecisionOut.model_validate(decision)


@router.get("/{gate_key}/decisions", response_model=list[GateDecisionOut])
def list_gate_decisions(
    gate_key: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> list[GateDecisionOut]:
    _require_gate(db, gate_key)
    return [GateDecisionOut.model_validate(d) for d in list_decisions(db, gate_key)]


# ---------------------------------------------------------------------------
# Approvals
# ---------------------------------------------------------------------------


@router.post(
    "/decisions/{decision_id}/approve",
    response_model=ApprovalOut,
    status_code=status.HTTP_201_CREATED,
)
def approve_decision(
    decision_id: uuid.UUID,
    body: ApprovalCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[str, Depends(get_actor)],
) -> ApprovalOut:
    decision = _require_decision(db, decision_id)
    try:
        approval = apply_approval(
            db, decision=decision, action=body.action, justification=body.justification, actor=actor
        )
    except ApprovalError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return ApprovalOut.model_validate(approval)
