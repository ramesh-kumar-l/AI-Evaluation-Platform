# Contributing to AI Evaluation Platform

Thank you for your interest in contributing to AEP. This guide covers everything you need
to make a meaningful contribution.

---

## Before You Start

**Read these first:**
1. `project-memory-bank/active-context.md` — current save-state (what's done, open threads)
2. `project-memory-bank/implementation-status.md` — per-phase completion checklist
3. `docs/NewbieQuickStarterGuide.md` — full onboarding (if you haven't already)
4. `project-memory-bank/projectbrief.md` — non-negotiable principles

**Check for duplicates:** Search open issues and PRs before starting.

---

## Project Principles (non-negotiable)

These principles apply to every contribution:

1. **Trust > Intelligence** — every result must be verifiable, never a black box.
2. **Offline-first** — every workflow must run with Ollama + SQLite, no cloud.
3. **Reproducibility > Novelty** — every result must be reproducible from versioned inputs.
4. **Simplicity** — minimum code that solves the problem. No speculative abstractions.
5. **Surgical changes** — touch only what the task requires. Don't improve adjacent code.

---

## Development Setup

```bash
git clone https://github.com/your-org/ai-evaluation-platform
cd ai-evaluation-platform/backend

uv venv --python 3.12 .venv
uv pip install -e ".[dev]"

# Windows
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m pytest  # should be 150 passed

# macOS/Linux
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m pytest
```

---

## Code Standards

### File size
**Files must stay under 300 lines.** If a file is growing, split it by domain:
`evaluation_service.py` → `evaluation_service.py` + `evaluation_scoring.py`.

### Layering (strict)
```
api/      ← HTTP only: parse request, call service, return response
services/ ← Business logic, versioning, scoring, state machines, audit
models/   ← SQLAlchemy ORM definitions only
```
**Routers never call the database directly.** Services own all transactions.

### One concern per file
- `models/dataset.py` — Dataset model only
- `services/dataset_service.py` — Dataset service only
- `schemas/dataset.py` — Dataset schemas only

### Type annotations
`mypy --strict` runs on all 117 source files. Every new file must be fully typed.
No `# type: ignore` without a comment explaining why it's unavoidable.

### Tests
Every new endpoint, service function, and scorer needs tests. AEP tests are
integration-style — they use a real (in-memory SQLite) database and the FastAPI test client.
No mocking of the database layer.

---

## Quality Gates (all must pass)

```bash
# Linting + formatting
.venv/Scripts/ruff check .

# Static typing
.venv/Scripts/python -m mypy app

# Tests
.venv/Scripts/python -m pytest

# Schema drift check (must show no differences)
.venv/Scripts/python -m alembic check
```

All four must be green before any PR will be merged.

---

## Adding a Schema Change

1. Modify the model in `app/models/<entity>.py`
2. Generate a migration:
   ```bash
   .venv/Scripts/python -m alembic revision --autogenerate -m "describe_change"
   ```
3. **Review the generated migration** — autogenerate is a starting point, not a final answer.
   Check for: correct table names, indexes, nullable constraints, foreign keys.
4. Run `alembic upgrade head` and verify the migration applies cleanly.
5. Run `alembic check` — must show no differences.

**Never modify existing migration files.** Only add new ones.

---

## Architecture Decision Records (ADRs)

For significant architectural changes, write an ADR before implementing:

```
project-memory-bank/architecture-decisions/ADR-NNNN-<slug>.md
```

Use `ADR-0001-foundations.md` as a template. Open a PR with `[ADR]` in the title.
Get maintainer approval before implementing.

ADRs are required for:
- New dependencies
- Data model taxonomy changes
- Auth model changes
- New design patterns
- Deprecations

---

## Commit Style

```
<type>(<scope>): <short description>

<body — explain WHY, not WHAT>
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

Examples:
```
feat(rag): add faithfulness scorer using overlap coefficient
fix(rate-limit): clear _windows dict between tests to prevent stale state
docs(onboarding): add debugging guide and common mistakes section
```

---

## Pull Request Checklist

Before requesting review, verify:

- [ ] All 4 quality gates green (`ruff`, `mypy`, `pytest`, `alembic check`)
- [ ] Tests added for all new behavior (new endpoint → new test, new scorer → new test)
- [ ] Migration included for any schema change
- [ ] Files under 300 lines
- [ ] No unused imports (ruff catches them)
- [ ] No `type: ignore` without explanation
- [ ] ADR written if architecturally significant
- [ ] `project-memory-bank/active-context.md` updated if phase-level work
- [ ] `project-memory-bank/implementation-status.md` updated

---

## What NOT to Do

- Don't add error handling for impossible scenarios
- Don't add features beyond what the task requires
- Don't refactor adjacent code that isn't broken
- Don't add abstractions for single-use code
- Don't skip the quality gates (`--no-verify`, etc.)
- Don't modify existing migration files
- Don't hardcode credentials or secrets
- Don't add `print()` statements (use `get_logger(__name__).info(...)`)

---

## Reporting Issues

Use GitHub Issues. Include:
1. AEP version / commit hash
2. Operating system
3. Python version (`python --version`)
4. Steps to reproduce
5. Expected vs. actual behavior
6. Relevant logs (with secrets redacted)

---

## Security Issues

**Do not open a public GitHub issue for security vulnerabilities.**
See [SECURITY.md](./SECURITY.md) for the responsible disclosure process.

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
