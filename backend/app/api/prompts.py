"""Prompt endpoints (versioned create/read)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_actor
from app.core.database import get_db
from app.models.prompt import Prompt
from app.schemas.prompt import PromptCreate, PromptOut
from app.services import prompt_service, versioning

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.post("", response_model=PromptOut, status_code=201)
def create_prompt(
    body: PromptCreate, db: Session = Depends(get_db), actor: str = Depends(get_actor)
) -> Prompt:
    return prompt_service.create_prompt(db, data=body.model_dump(), actor=actor)


@router.post("/{key}/versions", response_model=PromptOut, status_code=201)
def revise_prompt(
    key: uuid.UUID,
    body: PromptCreate,
    db: Session = Depends(get_db),
    actor: str = Depends(get_actor),
) -> Prompt:
    try:
        return prompt_service.create_prompt(db, data=body.model_dump(), actor=actor, key=key)
    except versioning.EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_model=list[PromptOut])
def list_prompts(db: Session = Depends(get_db)) -> list[Prompt]:
    return versioning.list_latest(db, Prompt)


@router.get("/{key}", response_model=PromptOut)
def get_prompt(key: uuid.UUID, db: Session = Depends(get_db)) -> Prompt:
    prompt = versioning.get_latest(db, Prompt, key)
    if prompt is None:
        raise HTTPException(status_code=404, detail="prompt not found")
    return prompt


@router.get("/{key}/versions", response_model=list[PromptOut])
def list_prompt_versions(key: uuid.UUID, db: Session = Depends(get_db)) -> list[Prompt]:
    return versioning.list_versions(db, Prompt, key)
