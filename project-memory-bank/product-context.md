# Product Context

## Why AEP exists
Teams ship AI systems without a trustworthy, reproducible way to answer *"is this safe to release?"*.
Ad-hoc eval scripts produce numbers nobody can reproduce, audit, or defend. AEP makes AI quality a
**system of record**: versioned inputs, reproducible evaluations, detected regressions, and an
auditable release gate with human approval.

## Who uses it
- **ML/AI engineers** — run evaluations, compare models/prompts, investigate regressions.
- **Release owners / approvers** — read the gate decision, approve or override (with justification).
- **Auditors / governance** — replay any decision from immutable, versioned evidence.

## Core user journeys (MVP)
1. Register a versioned dataset, prompt, and model.
2. Run an evaluation offline against an Ollama model; metrics are computed and stored with provenance.
3. View results with **all** trust fields visible.
4. Compare two evaluations; detect and explain regressions.
5. Configure a release gate; get a block/allow decision; approve or override — fully audited.

## Explicitly out of scope (MVP)
- Performing the actual deployment (AEP records the *decision*, not the rollout).
- RAG / agent / tool evaluation (Milestone 2).
- Continuous/scheduled evaluation and full observability dashboards (Milestone 2).

## Experience principles
- Nothing is shown without its provenance.
- The system never silently overrides a human; overrides are explicit, justified, and logged.
- Works on a laptop with no internet.
