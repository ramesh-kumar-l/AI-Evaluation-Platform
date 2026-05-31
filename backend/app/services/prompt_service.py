"""Prompt service: create/revise versioned prompts."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.prompt import Prompt
from app.services import versioning


def create_prompt(
    db: Session, *, data: dict[str, Any], actor: str, key: uuid.UUID | None = None
) -> Prompt:
    return versioning.create_version(db, Prompt, fields=data, actor=actor, entity_key=key)
