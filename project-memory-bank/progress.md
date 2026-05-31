# Progress — Phased Delivery Roadmap (source of truth)

This is the durable copy of the **approved** phased roadmap. Phase-level granularity; detailed task
breakdowns are produced when each phase is individually approved.

## Milestone 1 — Walking Skeleton → Release Gate (MVP)

| Phase | Objective | Exit criteria | Status |
|-------|-----------|---------------|--------|
| **P0** Foundations & Memory Bank | Source of truth + minimal runnable scaffold | Empty app boots offline; CI green; memory bank populated | ✅ Complete |
| **P1** Core Domain Model & Versioning | Immutable, versioned, auditable entities | Versioned dataset/prompt/model with lineage + audit via API | ✅ Complete |
| **P2** Provider Abstraction & Offline Execution | Run a model deterministically, offline | Offline single-inference round-trip persisted & reproducible | ✅ Complete |
| **P3** Evaluation Engine + Metrics | Runs → scored, trust-annotated evaluations | Dataset-level eval yields reproducible scored results | ✅ Complete |
| **P4** Trust-First Result UI | Results visible, verifiable, auditable | Every mandated trust field shown for a real evaluation | 🟡 Authored |
| **P5** Comparison & Regression Detection | "Did it improve / regress?" | Regression detected, shown with evidence, recorded | ✅ Complete (backend) / 🟡 UI authored |
| **P6** Release Gates & Approvals → **MVP** | "Can we safely deploy?" | End-to-end dataset→eval→compare→gate→approval, audited | ✅ Complete (backend) / 🟡 UI authored |

## Milestone 2 — Depth & Breadth (post-MVP)
- **P7** Dataset & Benchmark Governance ✅ Complete (backend) / 🟡 UI authored
- **P8** RAG Evaluation ✅ Complete (backend) / 🟡 UI authored
- **P9** Agent & Tool Evaluation ✅ Complete (backend) / 🟡 UI authored
- **P10** Observability & Continuous Evaluation ✅ Complete (backend) / 🟡 UI authored
- **P11** Governance, Security, Accessibility, Docs & Deployment Hardening

## Dependency graph
```
P0 → P1 → P2 → P3 → P4 → P5 → P6  ==  MVP
                                  → P7 → P8 → P9 → P10 → P11
```
Strictly linear through the MVP. STOP for review at each phase boundary.

## Execution protocol
- Work only on the approved phase; never anticipate future phases.
- After each phase: update the memory bank, produce a completion report, STOP for review.
- See [implementation-status.md](./implementation-status.md) for the detailed save-state.
