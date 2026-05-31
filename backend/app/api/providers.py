"""Provider and Model endpoints (versioned create/read)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_actor
from app.core.database import get_db
from app.models.provider import Model, Provider
from app.schemas.provider import ModelCreate, ModelOut, ProviderCreate, ProviderOut
from app.services import provider_service, versioning

router = APIRouter(prefix="/providers", tags=["providers"])


@router.post("", response_model=ProviderOut, status_code=201)
def create_provider(
    body: ProviderCreate, db: Session = Depends(get_db), actor: str = Depends(get_actor)
) -> Provider:
    return provider_service.create_provider(db, data=body.model_dump(), actor=actor)


@router.post("/{key}/versions", response_model=ProviderOut, status_code=201)
def revise_provider(
    key: uuid.UUID,
    body: ProviderCreate,
    db: Session = Depends(get_db),
    actor: str = Depends(get_actor),
) -> Provider:
    try:
        return provider_service.create_provider(db, data=body.model_dump(), actor=actor, key=key)
    except versioning.EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_model=list[ProviderOut])
def list_providers(db: Session = Depends(get_db)) -> list[Provider]:
    return versioning.list_latest(db, Provider)


@router.get("/{key}", response_model=ProviderOut)
def get_provider(key: uuid.UUID, db: Session = Depends(get_db)) -> Provider:
    provider = versioning.get_latest(db, Provider, key)
    if provider is None:
        raise HTTPException(status_code=404, detail="provider not found")
    return provider


@router.get("/{key}/versions", response_model=list[ProviderOut])
def list_provider_versions(key: uuid.UUID, db: Session = Depends(get_db)) -> list[Provider]:
    return versioning.list_versions(db, Provider, key)


# --- Models ---


@router.post("/models", response_model=ModelOut, status_code=201, tags=["models"])
def create_model(
    body: ModelCreate, db: Session = Depends(get_db), actor: str = Depends(get_actor)
) -> Model:
    return provider_service.create_model(db, data=body.model_dump(), actor=actor)


@router.get("/models/{key}", response_model=ModelOut, tags=["models"])
def get_model(key: uuid.UUID, db: Session = Depends(get_db)) -> Model:
    model = versioning.get_latest(db, Model, key)
    if model is None:
        raise HTTPException(status_code=404, detail="model not found")
    return model
