"""Admin endpoints for API key management.

Protected by ``X-Admin-Secret`` header (value must match ``AEP_ADMIN_SECRET``).
This separate credential bootstraps the first API key when no keys exist yet.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.auth import ApiKeyCreate, ApiKeyCreatedOut, ApiKeyOut
from app.services import auth_service

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin_secret(
    x_admin_secret: Annotated[str | None, Header()] = None,
) -> None:
    """Verify the admin bootstrap secret. Short-circuits if auth is disabled."""
    settings = get_settings()
    if not settings.api_auth_enabled:
        return
    if not settings.admin_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin secret not configured (set AEP_ADMIN_SECRET)",
        )
    if x_admin_secret != settings.admin_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Admin-Secret header",
        )


@router.post(
    "/api-keys",
    response_model=ApiKeyCreatedOut,
    status_code=201,
    dependencies=[Depends(_require_admin_secret)],
    summary="Create an API key (returned once — store it securely)",
)
def create_api_key(
    body: ApiKeyCreate,
    db: Annotated[Session, Depends(get_db)],
) -> ApiKeyCreatedOut:
    raw, key = auth_service.create_key(db, name=body.name, role=body.role)
    return ApiKeyCreatedOut(
        id=key.id,
        name=key.name,
        role=key.role,
        raw_key=raw,
        created_at=key.created_at,
    )


@router.get(
    "/api-keys",
    response_model=list[ApiKeyOut],
    dependencies=[Depends(_require_admin_secret)],
    summary="List all API keys (hashed — raw key not shown)",
)
def list_api_keys(
    db: Annotated[Session, Depends(get_db)],
) -> list[ApiKeyOut]:
    keys = auth_service.list_keys(db)
    return [
        ApiKeyOut(
            id=k.id,
            name=k.name,
            role=k.role,
            key_last4=k.key_hash[-4:],
            created_at=k.created_at,
            revoked_at=k.revoked_at,
        )
        for k in keys
    ]


@router.delete(
    "/api-keys/{key_id}",
    status_code=204,
    dependencies=[Depends(_require_admin_secret)],
    summary="Revoke an API key",
)
def revoke_api_key(
    key_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    key = auth_service.revoke_key(db, key_id)
    if key is None:
        raise HTTPException(status_code=404, detail="Key not found or already revoked")
