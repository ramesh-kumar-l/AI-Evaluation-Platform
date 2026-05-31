"""Shared API dependencies."""

from __future__ import annotations

from fastapi import Header


def get_actor(x_actor: str | None = Header(default=None)) -> str:
    """Identify who performed an action for the audit trail.

    Until RBAC lands (Phase 11), the actor comes from the ``X-Actor`` header, defaulting to
    ``"system"``. Every mutation is still attributed and audited.
    """
    return x_actor or "system"
