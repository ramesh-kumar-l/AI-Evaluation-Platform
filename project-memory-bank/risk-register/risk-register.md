# Risk Register

| ID | Risk | Phase | Mitigation | Status |
|----|------|-------|------------|--------|
| R1 | Temporal infra conflicts with offline mandate | P3 | In-process orchestration fallback; no cluster needed for dev/offline | Open |
| R2 | Versioning/immutability retrofit is costly if added late | P1 | Establish immutable versioning before any feature depends on mutable data | Open |
| R3 | Trust-field completeness drifts | P4 | Treat the AEP "Trust-First UI" field list as an explicit P4 exit checklist | Open |
| R4 | Scope creep into future phases | all | Phase-execution protocol: STOP at boundaries; detailed tasks only at approval | Open |
| R5 | Python 3.14 host may lack wheels for some deps | P0 | Pin to widely-supported versions; SQLite fallback avoids DB-driver friction in dev | Open |
| R6 | Frontend full build (Tauri/Rust) not verifiable without toolchain/network | P0 | Scaffold config + shell as files; defer build verification to when toolchain is present | Open |
