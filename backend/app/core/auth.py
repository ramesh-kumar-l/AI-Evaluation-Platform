"""FastAPI dependency for API key authentication.

When ``AEP_API_AUTH_ENABLED=false`` (default for local/test), all requests are admitted as
anonymous and ``get_current_key`` returns ``None``. Set it to ``true`` in production and every
request (except /health and /ready) must carry a valid ``X-API-Key`` header.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.api_key import ApiKey
from app.services import auth_service


def get_current_key(
    x_api_key: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
) -> ApiKey | None:
    """Return the authenticated ApiKey, or None when auth is disabled.

    Raises 401 if auth is enabled and the header is absent.
    Raises 403 if the key is unknown or has been revoked.
    """
    settings = get_settings()
    if not settings.api_auth_enabled:
        return None

    if x_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    key = auth_service.get_key_by_raw(db, x_api_key)
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or revoked API key",
        )
    return key


CurrentKey = Annotated[ApiKey | None, Depends(get_current_key)]
