"""Adapter registry: resolve a ProviderAdapter by provider kind."""

from __future__ import annotations

from app.services.providers.base import ProviderAdapter
from app.services.providers.ollama import OllamaAdapter

_KIND_TO_CLS: dict[str, type[OllamaAdapter]] = {
    "ollama": OllamaAdapter,
}


def get_adapter(kind: str, base_url: str) -> ProviderAdapter:
    """Return a concrete adapter instance for *kind*.

    Cloud adapters (openai, anthropic, …) are gated behind ``enable_cloud_providers``
    and will be registered here in a future phase.
    """
    cls = _KIND_TO_CLS.get(kind)
    if cls is None:
        supported = list(_KIND_TO_CLS)
        raise ValueError(f"Unsupported provider kind: {kind!r}. Supported: {supported}")
    return cls(base_url=base_url)
