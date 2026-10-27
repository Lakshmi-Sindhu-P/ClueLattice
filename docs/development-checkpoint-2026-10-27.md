# Development Checkpoint — 2026-10-27 (controlled pause)

Requested pause (m01701): no new development tasks until explicit resume authorization.

## 1. Where work stopped

- **Current branch:** `research/vvs-p0-2-e2e-demonstrations` (stacked on `research/vvs-p0-1-claim-resolution`).
- **HEAD at checkpoint:** this commit (P0.2 deliverable + this file) atop `aa5a3df`
  (`test(verification): prove resolver-layer reference checks end-to-end for #34`), which atop
  `main` = `c8a3828` (`merge: research/egress-approval — freeze flipped to HUMAN_APPROVED`).
- **Stopped mid-P0:** P0.1 done; P0.2 finished and verified at the moment of pause (full gates run
  recorded below); P0.3–P0.7 of the approved plan v2 not started.
- **Worktree:** clean except untracked `kathmandu/.uv-cache/` (uv cache dir, intentionally left
  untouched; should be gitignored in a later session).

## 2. Preservation state

- **Schedules / crons:** none registered (`cron_list` empty, `schedule_list` empty).
- **Autonomous continuation:** orchestrator goal `goal-da35a498…` set to **phase `paused`**
  (revision 2, activation disarmed). Resume requires explicit human authorization.
- **Durable queue:** untouched this session — no `workflow_claim` / `workflow_complete` /
  `workflow_enqueue`; retry history and queued jobs preserved; no jobs deleted.
- **Jobs:** no running background jobs at pause (gates job `bash-7522defe3812442c` completed;
  an earlier probe job `bash-73401c637a1b45bc` completed having failed harmlessly at import time —
  `python -m src.cluelattice.experiments.pipeline` does not exist; it wrote nothing).
- **Sealed Scenario 7 / frozen protocols / datasets / evidence artifacts:** unmodified —
  `git status` empty for `data/`, `configs/`, `docs/` tracked files; freeze artifact stays
  `HUMAN_APPROVED` as merged in `c8a3828`; safety tag `pre-cluelattice-rename` intact.
- **Worktree at pause:** exactly the 4 files of this checkpoint (3 P0.2 deliverables + this file);
  uv cache is kept outside the repo (workspace `.uvcache/`), no stray artifacts.
- **Credentials:** never read or written; no secrets in any commit (secret scan clean earlier).
- **GitHub:** `origin/main` == `main`; checkpoint pushes touch only `research/*` branches.

## 3. P0 status (approved plan v2)

| Item | State | Evidence |
| --- | --- | --- |
| P0.1 `verify_claim` reference handling (#34) | **DONE** (commit `aa5a3df`, issue #34 commented with executed results) | `tests/test_claim_verification_scope.py` 5 passed; `tests/test_ledger_evidence.py` 9 passed (CLI catch-test: fabricated ref → exit 1 `does not resolve`; positive control exit 0) |
| P0.2 three-class E2E demonstration | **DONE at pause, committed on this branch** | `uv run python scripts/demonstrate_evidence_outcomes.py` → exit 0, `expectations_met: true`, deterministic `record_sha256 = 7e477a1d…`, spine `d64a13fa…` ×2; `--forge-valid` → exit 1 (catch-test); wrapper 4 passed |
| P0.3 requirements-coverage map + checker | **PLANNED** | — |
| P0.4 fail-closed `validate_phase3_evidence` | **PLANNED** | — |
| P0.5 root-of-trust / pinned-tag verifier | **PLANNED** | — |
| P0.6 sealed-data boundary guard | **PLANNED** | — |
| P0.7 queue full-cycle rehearsal | **PLANNED** (queue deliberately untouched at pause) | — |
| P1.1–P1.5, P2.x | **PLANNED** (P2 needs explicit go + dependency approval) | — |

## 4. Latest test results (executed at checkpoint, 2026-10-27)

```bash
# full gates (all exit 0):
uv run pytest -q        # 606 passed, 1 warning in 24.10s; coverage 3651 stmts,
                        # 96.00% (≥90 gate) — PYTEST_EXIT=0
uv run ruff check .     # All checks passed! — exit 0
uv run mypy             # Success: no issues found in 54 source files — exit 0

# P0.2 demonstration (both modes, observed):
uv run python scripts/demonstrate_evidence_outcomes.py            # exit 0
uv run python scripts/demonstrate_evidence_outcomes.py --forge-valid  # exit 1 (expected)

# targeted P0.1+P0.2 tests (subset, coverage off):
uv run pytest -q -o addopts= tests/test_evidence_outcome_demonstration.py \
  tests/test_ledger_evidence.py tests/test_claim_verification_scope.py  # 18 passed
```

Note: CI (`.github/workflows/ci.yml`) runs `ruff check .` + `mypy` (scope `files = ["src"]`) +
pytest. `mypy` on `scripts/` is out of gate: the new runner has 2 `import-untyped` errors
(cluelattice ships no `py.typed`; 5 pre-existing sibling script errors share this cause).

## 5. Module inventory (purpose · key decisions · remaining work)

| Module | Purpose | Depends on | Notes / remaining |
| --- | --- | --- | --- |
| `src/cluelattice/schemas` | Pydantic domain model: events, findings, claims, manifests, review, triage | pydantic, uuid5 namespaces | v2 id namespaces (rename re-versioned); v1 frozen on old base |
| `src/cluelattice/verification` | `verify_claim` kind-vs-resolution contract + `evidence_assertions` path resolver | schemas | **known limit:** no URI resolver for `EvidenceReference` (issue #34, deliberately not invented); optional `resolution_checked` field = open decision |
| `src/cluelattice/ingestion` | pcap/CSV flows, CTU-13 / IOT-23 ingest scripts | pandas, pyarrow | frozen datasets untouched |
| `src/cluelattice/features` | 43-feature extraction, order-invariance pins | ingestion | issue-22 pins re-versioned at rename (A/B-proven id-only change) |
| `src/cluelattice/detection` | rule/baseline detectors | features | phase-3 baselines scripts |
| `src/cluelattice/triage` | LLM triage adapters, `INSUFFICIENT_EVIDENCE` path, comparisons | schemas, storage | issues #32/#33 (argument-order sample, left/right evidence) open |
| `src/cluelattice/spine` | workflow spine records, offline demo runner | schemas | demo = mechanical stubs (stated in output) |
| `src/cluelattice/storage` | artifact bundles, results ledger, registry | schemas | ledger validator fail-closed under `--require-artifacts` |
| `src/cluelattice/review` | review history / packet | storage | sealed `review-packet/` hash-frozen (rename deviation documented) |
| `src/cluelattice/ui` | FastAPI/Streamlit analyst UI | storage, triage | UI extras need `[ui]` (CI fix `422050a`) |
| `src/cluelattice/evaluation`, `detection`, `config`, `logging_config` | eval harness, config, structured logging | — | config env prefix `CLUELATTICE_*` |
| `scripts/validate_*.py` (7 validators) + `verify_artifact_manifest.py` | evidence-engine gates | storage/schemas | fail-closed P0.4 hardening = remaining |
| `scripts/demonstrate_evidence_outcomes.py` + `tests/test_evidence_outcome_demonstration.py` | P0.2 three-class executable demonstration + non-vacuity flip | above CLIs, pytest subprocesses | out of mypy gate (see §4) |
| `tests/` (606 tests, 96% cov) | unit + CLI E2E + adversarial falsification suite | pytest | — |

## 6. Outstanding defects / blockers

- GitHub open issues: **#45** (commit review-packet artifact), **#34** (partially addressed by
  P0.1 — kind vs existence; comment posted, still open), **#33**, **#32**, **#27** (stability
  artifact provenance), **#11** (LLM eval corpus / provider freeze / A/B — needs live model access),
  **#10** (analyst-outcome program).
- **No live-model A/B run** — freeze is `HUMAN_APPROVED` for egress but the experiment has not
  been executed; requires model credentials (OpenCode API key decision pending).
- **No in-repo pipeline-node runner:** `python -m src.cluelattice.experiments.pipeline` does not
  exist; “E2E nodes” are pytest invocations only. Do not cite a node runner until one is built.
- mypy `scripts/` out-of-gate (`py.typed` packaging decision) · plan v2 P0.3–P0.7 and P1/P2 pending.

## 7. Resume steps (when explicitly authorized)

1. `update_goal action=resume` (goal id `goal-da35a498-5823-4ba9-b2f8-e07733276de1`, revision 2) or
   receive fresh instructions; confirm queue health with `workflow_status`.
2. Verify branches pushed (`git push origin research/vvs-p0-1-claim-resolution
   research/vvs-p0-2-e2e-demonstrations`), then merge P0.1+P0.2 stack to `main` only after CI green
   on a pushed state.
3. Continue plan v2: P0.3 → P0.4 → P0.5 → P0.6 → P0.7 (queue rehearsal last; no new crons without
   explicit re-approval), each on `research/vvs-*` with catch-test + linked issue per AGENTS.md.
4. Deferred decisions to surface: OpenCode API key provisioning; live A/B execution approval;
   `resolution_checked` schema field; `py.typed` marker; gitignore `.uv-cache`.
