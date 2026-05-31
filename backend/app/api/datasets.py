"""Dataset endpoints (versioned create/read) and dataset governance policy."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_actor
from app.core.database import get_db
from app.models.dataset import Dataset
from app.schemas.dataset import DatasetCreate, DatasetOut
from app.schemas.dataset_policy import DatasetPolicyOut, DatasetPolicyUpsert
from app.services import dataset_service, versioning
from app.services.dataset_policy_service import PolicyError, get_policy, upsert_policy

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


# ---------------------------------------------------------------------------
# Dataset governance policy
# ---------------------------------------------------------------------------


@router.put(
    "/{dataset_key}/policy", response_model=DatasetPolicyOut, status_code=status.HTTP_200_OK
)
def upsert_dataset_policy(
    dataset_key: uuid.UUID,
    body: DatasetPolicyUpsert,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[str, Depends(get_actor)],
) -> DatasetPolicyOut:
    try:
        policy = upsert_policy(
            db,
            dataset_key=dataset_key,
            owner=body.owner,
            status=body.status,
            quality_rules=body.quality_rules,
            ground_truth_policy=body.ground_truth_policy,
            notes=body.notes,
            actor=actor,
        )
    except PolicyError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return DatasetPolicyOut.model_validate(policy)


@router.get("/{dataset_key}/policy", response_model=DatasetPolicyOut)
def get_dataset_policy(
    dataset_key: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> DatasetPolicyOut:
    policy = get_policy(db, dataset_key)
    if policy is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"No policy for dataset {dataset_key}"
        )
    return DatasetPolicyOut.model_validate(policy)
