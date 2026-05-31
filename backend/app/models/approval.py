"""Approval: immutable record of a human action on a GateDecision.

action values:
  - "approved"   — pending_approval decision is approved; gate is cleared
  - "rejected"   — pending_approval decision is rejected; candidate cannot deploy
  - "overridden" — failed decision overridden with mandatory justification
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    decision_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)

    # "approved" | "rejected" | "overridden"
    action: Mapped[str] = mapped_column(String(32), nullable=False)

    # Human-provided rationale (mandatory; min 10 chars enforced in schema)
    justification: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="system")
