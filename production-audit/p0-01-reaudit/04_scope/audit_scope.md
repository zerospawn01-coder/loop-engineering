# P0-01 Re-Audit Scope

## In Scope

- `canary-fixture.schema.json` at the manifest `source_revision`.
- `auditor-result.schema.json` at the manifest `source_revision`.
- PATCH-01: `evidence_state` <-> `evidence_files` consistency.
- PATCH-02: `audit_status` <-> `observations` / `evidence_gaps` exclusivity.
- PATCH-03: explicit trust boundary for Auditor authority self-declarations.
- P0-01-GATE-01..12 execution evidence.
- Acceptance of valid reference cases.
- Search for closed-schema bypass, fixture-class/status semantic bypass, evidence-state contradiction, result-status payload contradiction, authority-boundary semantic drift, scope leakage, and newly introduced policy dilution.

## Out of Scope

- P0-02 Initial Canary Corpus.
- P0-03 Deterministic Qualifier implementation.
- P0.5 Finding Remediation & Closure implementation.
- Gemini/API orchestration automation.
- Design of fixes or remediation strategies.
- Regression-test implementation by the Auditor.
- Canonical LE verdict assignment by the Auditor.
- Self-hosting.

## Auditor Output Boundary

Allowed audit statuses only:

- `COUNTEREXAMPLE_FOUND`
- `NO_COUNTEREXAMPLE_FOUND`
- `INCONCLUSIVE`

The Auditor may search for Candidate Counterexamples only. It must not design a fix, identify remediation strategy, write tests, or assign PASS/FAIL/HOLD/BLOCKED to the audited subject.
