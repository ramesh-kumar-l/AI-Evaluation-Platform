"""Approval service: approve, reject, or override a GateDecision."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.approval import Approval
from app.models.gate_decision import GateDecision
from app.services import audit

# Valid (action, current_status) transitions
_VALID_TRANSITIONS: dict[str, set[str]] = {
    "approved": {"pending_approval"},
    "rejected": {"pending_approval"},
    "overridden": {"failed"},
}


class ApprovalError(Exception):
    """Raised when an approval action cannot proceed."""


def apply_approval(
    db: Session,
    *,
    decision: GateDecision,
    action: str,
    justification: str,
    actor: str,
) -> Approval:
    """Record a human approval action and update the GateDecision status."""
    allowed_statuses = _VALID_TRANSITIONS.get(action, set())
    if decision.status not in allowed_statuses:
        raise ApprovalError(
            f"Cannot apply action '{action}' to a decision with status '{decision.status}'. "
            f"Expected status in: {sorted(allowed_statuses)}"
        )

    previous_status = decision.status

    # Update decision status (mutable state transition)
    if action == "overridden":
        decision.status = "overridden"
        decision.override = True
        decision.override_justification = justification
    else:
        decision.status = action  # "approved" or "rejected"

    now = datetime.now(UTC)
    approval = Approval(
        id=uuid.uuid4(),
        decision_id=decision.id,
        action=action,
        justification=justification,
        created_at=now,
        created_by=actor,
    )
    db.add(approval)
    db.flush()

    audit.record_event(
        db,
        actor=actor,
        action=action,
        entity_type="gate_decisions",
        entity_key=decision.id,
        entity_version_id=None,
        payload={
            "approval_id": str(approval.id),
            "gate_key": str(decision.gate_key),
            "comparison_id": str(decision.comparison_id),
            "previous_status": previous_status,
            "new_status": decision.status,
        },
    )
    db.commit()
    db.refresh(approval)
    return approval
