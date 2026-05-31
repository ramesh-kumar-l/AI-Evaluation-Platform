"""Dataset service: create/revise versioned datasets.

Derives ``item_count`` and keeps the audit payload light (a summary, not the full item list) so the
audit log stays compact while remaining verifiable.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.services import versioning


def create_dataset(
    db: Session, *, data: dict[str, Any], actor: str, key: uuid.UUID | None = None
) -> Dataset:
    items = data.get("items", [])
    fields = {**data, "item_count": len(items)}
    audit_payload = {
        "name": data.get("name"),
        "description": data.get("description", ""),
        "item_count": len(items),
    }
    return versioning.create_version(
        db, Dataset, fields=fields, actor=actor, entity_key=key, audit_payload=audit_payload
    )
