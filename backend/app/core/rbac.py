"""Role-based access control helpers.

Roles (weakest → strongest): viewer → evaluator → approver → admin.
When auth is disabled the role check is skipped entirely.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.core.auth import get_current_key
from app.models.api_key import ApiKey

# Role hierarchy: each level implies all roles to its left.
_ROLE_LEVEL: dict[str, int] = {
    "viewer": 0,
    "evaluator": 1,
    "approver": 2,
    "admin": 3,
}


def _level(role: str) -> int:
    return _ROLE_LEVEL.get(role, -1)


def require_role(minimum_role: str) -> Callable[[ApiKey | None], None]:
    """Dependency factory that enforces a minimum RBAC level.

    Usage::

        @router.post("/...", dependencies=[Depends(require_role("evaluator"))])
    """

    def _check(current_key: ApiKey | None = Depends(get_current_key)) -> None:
        if current_key is None:
            return  # auth disabled — allow all
        if _level(current_key.role) < _level(minimum_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_key.role}' is below the required '{minimum_role}' level",
            )

    return _check
