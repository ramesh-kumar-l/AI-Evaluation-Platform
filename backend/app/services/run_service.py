"""Run service: render prompt, execute inference, persist InferenceRun + audit event."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.prompt import Prompt
from app.models.provider import Model, Provider
from app.models.run import InferenceRun
from app.services import audit
from app.services.providers.base import InferenceRequest, ProviderError
from app.services.providers.registry import get_adapter


class RunError(Exception):
    """Raised for input errors that prevent a run from starting (e.g. missing template vars)."""


def _render_prompt(template: str, variables: dict[str, Any]) -> str:
    try:
        return template.format_map(variables)
    except KeyError as exc:
        raise RunError(f"Missing prompt variable: {exc}") from exc


def execute_run(
    db: Session,
    *,
    prompt: Prompt,
    model: Model,
    provider: Provider,
    input_variables: dict[str, Any],
    parameters: dict[str, Any],
    actor: str,
) -> InferenceRun:
    """Execute one inference, persist the run record, emit an audit event.

    Provider failures (Ollama down, HTTP errors) are captured as status="failed" rather than
    raised — the run is still persisted for auditability. Input errors (missing template
    variables, unsupported provider kind) raise RunError before any network call.
    """
    rendered = _render_prompt(prompt.template, input_variables)
    adapter = get_adapter(kind=provider.kind, base_url=provider.base_url)
    request = InferenceRequest(model=model.name, prompt=rendered, parameters=parameters)

    started_at = datetime.now(UTC)
    status = "completed"
    raw_output = ""
    error: str | None = None
    latency_ms = 0
    trace: dict[str, Any] = {
        "request": {
            "model": model.name,
            "prompt": rendered,
            "parameters": parameters,
        },
        "response": {},
    }

    try:
        response = adapter.infer(request)
        raw_output = response.output
        latency_ms = response.latency_ms
        trace["response"] = response.raw
    except ProviderError as exc:
        status = "failed"
        error = str(exc)

    completed_at = datetime.now(UTC)

    run = InferenceRun(
        id=uuid.uuid4(),
        created_at=started_at,
        created_by=actor,
        prompt_key=prompt.entity_key,
        model_key=model.entity_key,
        provider_key=provider.entity_key,
        prompt_version_id=prompt.id,
        model_version_id=model.id,
        provider_version_id=provider.id,
        rendered_prompt=rendered,
        raw_output=raw_output,
        parameters=parameters,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        latency_ms=latency_ms,
        error=error,
        trace=trace,
    )
    db.add(run)
    db.flush()

    audit.record_event(
        db,
        actor=actor,
        action="run",
        entity_type="inference_runs",
        entity_key=run.id,
        entity_version_id=None,
        payload={
            "status": status,
            "prompt_key": str(prompt.entity_key),
            "model_key": str(model.entity_key),
            "provider_key": str(provider.entity_key),
            "latency_ms": latency_ms,
        },
    )
    db.commit()
    db.refresh(run)
    return run
