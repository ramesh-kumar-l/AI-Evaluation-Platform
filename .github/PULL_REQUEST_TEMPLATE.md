# Pull Request

## What this PR does

<!-- 1-3 sentences. What changed and why. -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor (no functional change)
- [ ] Documentation
- [ ] Infrastructure / DevOps
- [ ] ADR (architectural decision)

## Quality gates

All must be green before merge:

- [ ] `ruff check .` — no lint errors
- [ ] `ruff format --check .` — no format issues
- [ ] `mypy app` — no type errors (--strict)
- [ ] `pytest` — all tests pass
- [ ] `alembic check` — no schema drift

## Checklist

- [ ] Tests added for all new behavior
- [ ] Migration included for schema changes (and reviewed — not just autogenerate output)
- [ ] Files under 300 lines
- [ ] No unused imports
- [ ] No `type: ignore` without explanation
- [ ] ADR written if architecturally significant
- [ ] `project-memory-bank/active-context.md` updated if phase-level work
- [ ] `project-memory-bank/implementation-status.md` updated

## Breaking changes

<!-- Does this change any existing API contracts, migration behavior, or config defaults?
     If yes, describe the impact and migration path. -->

## Screenshots / logs (if relevant)

<!-- For UI changes: before/after screenshots. For backend: relevant log output. -->
