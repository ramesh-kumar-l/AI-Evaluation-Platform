# Project Brief — AI Evaluation Platform (AEP)

## What this is
AEP is the **system of record for AI quality**: benchmarking, regression detection, release
assurance, and deployment trust. Its single product question is:

> **"Can we safely deploy?"**

## Non-negotiable principles
- **Trust > Intelligence** — every result is verifiable, never a black box.
- **Evidence > Confidence** — claims are backed by traceable evidence.
- **Governance > Automation** — humans approve; the system records and enforces.
- **Reproducibility > Novelty** — every result is reproducible from versioned inputs.
- **Explainability > Complexity** — a reviewer can always understand *why*.

## Hard mandates
- **Offline-first.** Every workflow must run with **Ollama** + a local Postgres, no cloud.
  Cloud providers are optional adapters behind feature flags — never a hard dependency.
- **Trust-first UI.** Every result displays: benchmark/dataset/model/prompt versions, timestamp,
  evaluation method, metric definitions, confidence level, approval status, audit history.
- **Auditable & reproducible.** Immutable versioned entities; append-only audit log; every
  mutation traceable.

## First milestone (MVP)
A walking skeleton — a thin but complete vertical slice from
**dataset → evaluation → comparison/regression → release-gate decision** with approvals and full
audit. Delivered across Phases 0–6. See [progress.md](./progress.md) for the full roadmap.
