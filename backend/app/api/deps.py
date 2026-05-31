"""Shared API dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header

from app.core.auth import get_current_key
from app.models.api_key import ApiKey


def get_actor(
    current_key: Annotated[ApiKey | None, Depends(get_current_key)],
    x_actor: str | None = Header(default=None),
) -> str:
    """Identify who performed an action for the audit trail.

    When auth is enabled the actor comes from the API key's name.
    When auth is disabled (local/test), falls back to the ``X-Actor`` header or ``"system"``.
    """
    if current_key is not None:
        return current_key.name
    return x_actor or "system"
