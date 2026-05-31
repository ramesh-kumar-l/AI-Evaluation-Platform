"""Dataset endpoints (versioned create/read)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_actor
from app.core.database import get_db
from app.models.dataset import Dataset
from app.schemas.dataset import DatasetCreate, DatasetOut
from app.services import dataset_service, versioning

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetOut, status_code=201)
def create_dataset(
    body: DatasetCreate, db: Session = Depends(get_db), actor: str = Depends(get_actor)
) -> Dataset:
    return dataset_service.create_dataset(db, data=body.model_dump(), actor=actor)


@router.post("/{key}/versions", response_model=DatasetOut, status_code=201)
def revise_dataset(
    key: uuid.UUID,
    body: DatasetCreate,
    db: Session = Depends(get_db),
    actor: str = Depends(get_actor),
) -> Dataset:
    try:
        return dataset_service.create_dataset(db, data=body.model_dump(), actor=actor, key=key)
    except versioning.EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_model=list[DatasetOut])
def list_datasets(db: Session = Depends(get_db)) -> list[Dataset]:
    return versioning.list_latest(db, Dataset)


@router.get("/{key}", response_model=DatasetOut)
def get_dataset(key: uuid.UUID, db: Session = Depends(get_db)) -> Dataset:
    dataset = versioning.get_latest(db, Dataset, key)
    if dataset is None:
        raise HTTPException(status_code=404, detail="dataset not found")
    return dataset


@router.get("/{key}/versions", response_model=list[DatasetOut])
def list_dataset_versions(key: uuid.UUID, db: Session = Depends(get_db)) -> list[Dataset]:
    return versioning.list_versions(db, Dataset, key)
