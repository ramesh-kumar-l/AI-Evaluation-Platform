"""API key lifecycle: creation, lookup, revocation."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.api_key import ApiKey

_PREFIX = "aep_"
_KEY_BYTES = 24  # 48 hex chars → 52 total with prefix


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def generate_raw_key() -> str:
    return _PREFIX + secrets.token_hex(_KEY_BYTES)


def create_key(db: Session, *, name: str, role: str) -> tuple[str, ApiKey]:
    """Create a new API key. Returns (raw_key, ApiKey) — raw key is NOT stored."""
    raw = generate_raw_key()
    api_key = ApiKey(
        id=uuid.uuid4(),
        name=name,
        key_hash=_hash_key(raw),
        role=role,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return raw, api_key


def get_key_by_raw(db: Session, raw: str) -> ApiKey | None:
    h = _hash_key(raw)
    return db.scalar(
        select(ApiKey).where(ApiKey.key_hash == h, ApiKey.revoked_at.is_(None))
    )


def revoke_key(db: Session, key_id: uuid.UUID) -> ApiKey | None:
    key = db.get(ApiKey, key_id)
    if key is None or key.revoked_at is not None:
        return None
    key.revoked_at = datetime.now(UTC)
    db.commit()
    db.refresh(key)
    return key


def list_keys(db: Session) -> list[ApiKey]:
    return list(db.scalars(select(ApiKey).order_by(ApiKey.created_at.asc())).all())
