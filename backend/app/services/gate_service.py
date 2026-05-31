"""Gate service: create release gates and evaluate them against comparisons."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.comparison import Comparison
from app.models.gate_decision import GateDecision
from app.models.release_gate import ReleaseGate
from app.services import audit
from app.services.versioning import create_version, get_latest, list_latest


class GateError(Exception):
    """Raised when a gate operation cannot proceed."""


def create_gate(
    db: Session,
    *,
    name: str,
    description: str,
    criteria: list[dict[str, Any]],
    max_regressions_allowed: int,
    require_approval: bool,
    notes: str | None,
    actor: str,
) -> ReleaseGate:
    return create_version(
        db,
        ReleaseGate,
        fields={
            "name": name,
            "description": description,
            "criteria": criteria,
            "max_regressions_allowed": max_regressions_allowed,
            "require_approval": require_approval,
            "notes": notes,
        },
        actor=actor,
        audit_payload={"name": name, "criteria_count": len(criteria)},
    )


def get_gate(db: Session, gate_key: uuid.UUID) -> ReleaseGate | None:
    return get_latest(db, ReleaseGate, gate_key)


def list_gates(db: Session) -> list[ReleaseGate]:
    return list_latest(db, ReleaseGate)


def evaluate_gate(
    db: Session,
    *,
    gate: ReleaseGate,
    comparison_id: uuid.UUID,
    actor: str,
) -> GateDecision:
    """Evaluate gate criteria against a comparison; persist + audit the GateDecision."""
    comparison = db.get(Comparison, comparison_id)
    if comparison is None:
        raise GateError(f"Comparison {comparison_id} not found")

    metric_deltas: dict[str, Any] = comparison.metric_deltas
    criteria_results: dict[str, Any] = {}
    passed_count = 0
    failed_count = 0

    for criterion in gate.criteria:
        mkey = str(criterion["metric_key"])
        min_score = float(criterion["min_score"])

        if mkey in metric_deltas:
            candidate_score = float(metric_deltas[mkey].get("candidate_score", 0.0))
            passed = candidate_score >= min_score
        else:
            candidate_score = 0.0
            passed = False

        criteria_results[mkey] = {
            "metric_key": mkey,
            "min_score": min_score,
            "candidate_score": round(candidate_score, 4),
            "passed": passed,
        }
        if passed:
            passed_count += 1
        else:
            failed_count += 1

    regressions_ok = comparison.regressions_detected <= gate.max_regressions_allowed
    raw_pass = failed_count == 0 and regressions_ok

    if raw_pass and gate.require_approval:
        status = "pending_approval"
    elif raw_pass:
        status = "passed"
    else:
        status = "failed"

    now = datetime.now(UTC)
    decision = GateDecision(
        id=uuid.uuid4(),
        gate_key=gate.entity_key,
        gate_version_id=gate.id,
        comparison_id=comparison_id,
        criteria_results=criteria_results,
        criteria_passed=passed_count,
        criteria_failed=failed_count,
        regressions_detected=comparison.regressions_detected,
        max_regressions_allowed=gate.max_regressions_allowed,
        status=status,
        override=False,
        override_justification=None,
        created_at=now,
        created_by=actor,
    )
    db.add(decision)
    db.flush()

    audit.record_event(
        db,
        actor=actor,
        action="evaluate",
        entity_type="release_gates",
        entity_key=gate.entity_key,
        entity_version_id=gate.id,
        payload={
            "decision_id": str(decision.id),
            "status": status,
            "criteria_passed": passed_count,
            "criteria_failed": failed_count,
            "comparison_id": str(comparison_id),
        },
    )
    db.commit()
    db.refresh(decision)
    return decision


def list_decisions(db: Session, gate_key: uuid.UUID) -> list[GateDecision]:
    stmt = (
        select(GateDecision)
        .where(GateDecision.gate_key == gate_key)
        .order_by(GateDecision.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())
