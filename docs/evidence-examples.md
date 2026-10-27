# Evidence examples — observed, executed records

**Status: OBSERVED.** Every record in this document was produced by running the repository's own
code on 2026-10-27; none of it is copied from `data/results/results_ledger.json` or hand-written
prose. Re-run any command to regenerate the record. The runner is
`scripts/demonstrate_evidence_outcomes.py`; its test wrapper is
`tests/test_evidence_outcome_demonstration.py`.

## Why this document exists

An unmodified ledger asserts things like `REFUTED (protocol, N=8: all 8 pairs disagree)` as static
text. That is a *claim* about execution, not *evidence from* execution. The project's three-class
model — **known-good / known-bad / insufficient-evidence** — needs worked examples where the
outcome class is produced by the code at a real boundary (CLI exit code, suite result, pipeline
node verdict), so a reviewer can rerun one command and watch each class happen.

One command produces all three legs:

```bash
npx --prefix . uv run python scripts/demonstrate_evidence_outcomes.py   # from kathmandu/
# or: uv run python scripts/demonstrate_evidence_outcomes.py
```

Exit code 0 means every leg met its expectation. The JSON record is deterministic: two consecutive
runs yield the same `record_sha256`.

## The three classes, as observed

### 1. known-good (exit 0, accepted)

Two independent genuine inputs, both accepted by the code paths that police them:

| Check | Boundary | Observed result |
| --- | --- | --- |
| Offline spine demo, twice, same `--created-at` | `scripts/run_offline_spine_demo.py` (CLI) | both runs exit 0; byte-identical output, `output_sha256 = d64a13fa9983bc37133c79350deb873f3f22b8315c61aad013c8e379a1c7d8db` |
| Genuine ledger fixture (correct evidence string + real artifact digest) | `scripts/validate_results_ledger.py --require-artifacts` (CLI) | exit 0 |

### 2. known-bad (non-zero, caught, with the violation named)

| Fixture | Boundary | Observed result |
| --- | --- | --- |
| Ledger whose evidence value was forged (`headline.best = false` recorded as `true`) | same validator CLI | **exit 1**, `violation_kind = "mismatch"` |
| Ledger citing a nonexistent artifact key | same validator CLI | **exit 1**, `violation_kind = "does not resolve"` |
| Every forged structure in the adversarial suite | `pytest tests/test_decision_falsification.py` (process) | exit 0 — i.e. the suite that *attacks* the validators passes, because each forgery is refused by the code it targets |

### 3. insufficient-evidence (legitimately recorded, never coerced)

| Check | Boundary | Observed result |
| --- | --- | --- |
| Real triage pipeline node admitting an `INSUFFICIENT_EVIDENCE` assessment as pending review | `pytest -o addopts= tests/test_triage.py::test_insufficient_evidence_is_admissible_end_to_end` (process) | exit 0 |
| Explicit abstention claim | `cluelattice.verification.verify_claim` (function) | `verified = True`, effective type stays `UNKNOWN_INSUFFICIENT_EVIDENCE` (not upgraded to supported) |
| Ledger claim with `status: UNKNOWN` | validator CLI | exit 0 — recorded as a legitimate claim, not forced into good or bad |

## The catch-test (why this demonstration cannot pass vacuously)

Flipping the forger to emit a *structurally valid* fixture must break the known-bad leg:

```bash
uv run python scripts/demonstrate_evidence_outcomes.py --forge-valid
# → expectations_met: false, forged_value_ledger exit 0, process exit 1
```

Observed on 2026-10-27: exit 1, `expectations_met = false`, forged leg observed acceptance
(`exit_code 0`) — exactly the failure the demonstration is supposed to expose if validators ever
stop catching forgeries. The test suite pins this flip
(`test_the_catch_test_forger_flip_fails_the_known_bad_leg`), so the demonstration degrades loudly,
not silently.

## Honest limits

- The spine leg uses **mechanical stub providers** — its output carries a warning saying so. It
  demonstrates determinism and seal/validate structure, not model quality.
- The ledger fixtures (genuine/forged/missing/unknown) are **synthetic artifacts written by the
  runner into a temp directory**; the genuine fixture is not a model-produced bundle.
- Nothing here executes the frozen experiment; the freeze remains sealed
  (`tests/test_freeze_prereg_seal.py`).
- What *is* real: the validators, the falsification suite, the triage node, the abstention claim
  path, and the spine demo — each at its actual process boundary.

## Full-suite gates

```bash
npx vitest run --config vitest.config.browser.ts   # browser test path (TSV-8695); observed exit 0
uv run pytest -q                                   # python suite (gates before any merge)
```
