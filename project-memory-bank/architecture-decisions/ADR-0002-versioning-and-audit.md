# ADR-0002 — Immutable Versioning & Append-Only Audit (Phase 1)

- **Status:** Accepted
- **Date:** 2026-05-31

## Context
Phase 1 must make domain entities immutable, versioned, auditable, and reproducible — the foundation
every later phase depends on. The roadmap lists many entities under Phase 1 scope, but several
(Evaluation, Run, Result, Approval, ReleaseGate, Benchmark, Metric) are only meaningfully *exercised*
in their owning phases (P2–P6).

## Decisions
1. **Generic versioning via a `VersionedMixin`.** Each logical entity has a stable `entity_key`;
   every change creates a **new immutable row** with an incremented `version`, a `parent_id` lineage
   pointer, and an `is_latest` flag. Rows are never updated in place (except flipping the previous
   `is_latest` to false).
2. **Append-only audit with a hash chain.** Every mutation writes an `AuditEvent` carrying a
   monotonic `seq`, the actor, the action, the entity reference, a JSON payload, and
   `hash = sha256(prev_hash + canonical_payload)`. This makes the log tamper-evident and is the
   backbone of "evidence > confidence".
3. **Build the foundation + the entities we can exercise end-to-end now.** Phase 1 fully implements
   Provider/Model, Prompt, and Dataset (model → schema → service → API → migration → tests) to meet
   the exit criteria. Remaining entities adopt the *same* `VersionedMixin` in their owning phases
   rather than being created as speculative empty tables now.
   - **Why:** avoids premature, likely-wrong schema design for P2–P6 (risk R4), keeps Phase 1
     verifiable, and costs nothing later because the mixin is entity-agnostic.

## Consequences
- A reviewer can reconstruct any entity's full history and verify the audit chain.
- Cross-DB: UUID/JSON via SQLAlchemy's portable types so the SQLite fallback and Postgres behave the
  same. `parent_id` is a lineage pointer (not a hard FK) to keep the mixin table-agnostic.
- Later phases extend the schema additively through Alembic; no retrofit of versioning/audit needed.
