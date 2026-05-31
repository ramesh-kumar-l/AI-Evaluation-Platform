"""Provider and Model domain entities (versioned).

A Provider is an inference backend (Ollama, OpenAI, …). A Model belongs to a provider by its stable
``provider_key`` (the provider's ``entity_key``), keeping the lineage independent of versions.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import JSON, Boolean, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.mixins import VersionedBase


class Provider(VersionedBase):
    __tablename__ = "providers"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # "ollama" is the mandatory offline default; cloud kinds are feature-flagged.
    kind: Mapped[str] = mapped_column(String(64), nullable=False, default="ollama")
    base_url: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class Model(VersionedBase):
    __tablename__ = "models"

    # Stable identity of the owning provider (its entity_key), not a specific provider version.
    provider_key: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
