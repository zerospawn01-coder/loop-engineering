# P0-01 Canary Fixture Contract — Re-Audit Normative Candidate v1

STATUS: FREEZE CANDIDATE / RE-AUDIT TARGET
SCOPE: P0-01 only

## 1. Contract artifacts

P0-01 defines exactly two subject schemas:

1. `auditor/canary/schema/canary-fixture.schema.json`
2. `auditor/canary/schema/auditor-result.schema.json`

P0-02 Initial Canary Corpus and P0-03 Deterministic Qualifier are outside this contract.

## 2. Canary fixture classification semantics

The fixture classes and their expected audit statuses are fixed:

- `POSITIVE` -> `COUNTEREXAMPLE_FOUND`
- `NEGATIVE` -> `NO_COUNTEREXAMPLE_FOUND`
- `AMBIGUOUS` -> `INCONCLUSIVE`

The fixture contract is closed: unknown top-level and nested fields are not admitted where the schema declares `additionalProperties: false`.

## 3. Evidence-state consistency

`evidence_state` and `evidence_files` must not contradict each other:

- `NONE` requires `evidence_files` to be empty.
- `COMPLETE` requires at least one `evidence_files` entry.
- `PARTIAL` is not given a numeric completeness threshold by P0-01.

Every file reference SHA-256 is represented by exactly 64 hexadecimal characters.

## 4. Auditor-result status semantics

The machine-readable result statuses are exactly:

- `COUNTEREXAMPLE_FOUND`
- `NO_COUNTEREXAMPLE_FOUND`
- `INCONCLUSIVE`

Payload semantics are exclusive:

- `COUNTEREXAMPLE_FOUND`: at least one `observation`; zero `evidence_gaps`.
- `NO_COUNTEREXAMPLE_FOUND`: zero `observations`; zero `evidence_gaps`.
- `INCONCLUSIVE`: zero `observations`; at least one `evidence_gap`.

## 5. Authority boundary

The `authority` object in `auditor-result.schema.json` contains Auditor self-declarations only.

It must require:

- `canonical_verdict_claimed == false`
- `canonical_verdict_value == null`
- `improvement_proposal_present == false`

These fields are not independent proof that the raw Auditor output contains no authority violation. Independent raw-output verification belongs to a later external qualification stage and is not implemented by P0-01.

## 6. P0-01 deterministic Gate set

- GATE-01: both schemas are valid JSON Schema Draft 2020-12 schemas.
- GATE-02: unknown top-level or nested properties are rejected.
- GATE-03: malformed SHA-256 values are rejected.
- GATE-04: `POSITIVE + NO_COUNTEREXAMPLE_FOUND` is rejected.
- GATE-05: `NEGATIVE + COUNTEREXAMPLE_FOUND` is rejected.
- GATE-06: `COUNTEREXAMPLE_FOUND + observations=[]` is rejected.
- GATE-07: `INCONCLUSIVE + evidence_gaps=[]` is rejected.
- GATE-08: authority self-declarations claiming a canonical verdict or an improvement proposal are rejected.
- GATE-09: `evidence_state=NONE` with non-empty `evidence_files` is rejected.
- GATE-10: `evidence_state=COMPLETE` with empty `evidence_files` is rejected.
- GATE-11: `INCONCLUSIVE` with non-empty `observations` is rejected.
- GATE-12: `COUNTEREXAMPLE_FOUND` with non-empty `evidence_gaps` is rejected.

The Gate runner must additionally demonstrate non-vacuity by accepting valid reference cases for all three fixture classes and all three Auditor result statuses.

## 7. Freeze boundary

Deterministic Gate success is necessary but not sufficient for P0-01 Freeze.

P0-01 Freeze requires:

1. the exact patched Subject revision,
2. deterministic Gate evidence and actual exit code,
3. source/evidence revision binding,
4. adversarial re-audit,
5. independent adjudication,
6. Human Authority freeze decision.

`NO_COUNTEREXAMPLE_FOUND` alone is never a Freeze decision.
