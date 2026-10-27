# ClueLattice

**Evidence-grounded AI security triage.** A research repository in which every claim the
documentation makes points at an artifact, a digest, and a ledger entry — including the claims
that were refuted, which stay in the ledger with their refutation attached.

MIT licensed. Defensive only: offline datasets, fixtures, and containers; no scanning of unowned
systems and no exploit tooling.

## At a glance

| | |
| --- | --- |
| **Status** | **Work in progress.** Phases 0–3 (ingestion, provenance, features, detectors, evaluation) are implemented and validated within the boundaries below; the triage layers that would make the system useful — finding aggregation, evidence retrieval, independent LLM review, and the human review tier — are designed and documented, not built. |
| **Question** | Can a provenance-first, multi-model triage system recommend security investigations without overstating what the telemetry shows? |
| **Data** | Licensed CTU-13 labeled text flows — Scenario 11: **107,251 rows accepted, 0 rejected**; Scenario 47: 558,912 / 7; Scenario 53: 325,471 / 0. An IoT-23 Zeek `conn.log` adapter is validated against safe synthetic fixtures. |
| **Bounded evidence** | Scenario-separated training/validation (107,251 / 129,832 / 114,077 rows), a sensitivity-frozen threshold of 0.20, a 450-policy reviewer sweep, and five registry-linked experiment runs. |
| **Strongest result** | Ranking alerts by model score retrieved at least as many true positives as threshold-distance "uncertainty" routing at **0 of 9 reviewer budgets on all six stage-1 captures** — a negative result that disputes a popular intuition and is kept, rather than deleted, in the ledger. |
| **What is not claimed** | No fusion, no LLM triage, no dashboard, no production use, no incident-detection or model-performance claim. Scenario 7 is the sealed holdout and may be opened once, after the policy is frozen. |
| **Verify it yourself** | [results ledger](docs/results.md) (machine-checked against the [experiment registry](docs/experiment_registry.json)) · [limitations](docs/limitations.md) · [resume evidence](docs/resume_evidence.md) · [artifact manifest](docs/artifact_manifest.json) |

## What this repository is

A single research question investigated in public, with the failure modes recorded as carefully
as the results: does a provenance-first system of specialists — deterministic rules, supervised
models, anomaly detection, temporal features — let a junior reviewer handle basic triage without
removing expert escalation?

The repository currently holds the defensible bottom half of that system, deliberately:

- **Ingestion and provenance** — two source adapters (IoT-23 Zeek, CTU-13 Argus) that emit typed
  canonical events, deterministic UUIDv5 identities, quality reports, and checksum-backed dataset
  manifests. 107,251 rows accepted from Scenario 11 with zero rejected or duplicated source rows.
- **Features under a leakage contract** — a 26-column `1.0.0` flow feature set, a `1.1.0`
  scenario-local behavioral family, and a `1.2.0` prior-only causal family, each version reviewed
  for temporal leakage and frozen before comparison.
- **Detectors and a comparison protocol** — three evidence-traceable flow rules, then a
  validation-only benchmark across rules, logistic regression, random forest, extra trees,
  histogram gradient boosting, and a linear SVM, with a sealed-scenario guard and per-case
  disagreement output.
- **A claim ledger** — every statement the project makes carries an evidence tier
  (`OBSERVED_FACT`, `DETERMINISTIC_DERIVATION`, `REFERENCE_BACKED_FACT`, `UNKNOWN_INSUFFICIENT_EVIDENCE`),
  the artifact that backs it, and an explicit statement of what it does **not** support. A validator
  fails the build if a claim drifts from its citation.

The parts that would make this operational — deterministic finding aggregation, evidence
retrieval, independent LLM review, and a human review tier — are planned and documented, not
implemented. That boundary is the point of the repository: it shows what the evidence currently
supports and what it would take to support more.

## Local Development

[`uv`](https://docs.astral.sh/uv/) provisions the pinned Python 3.12 interpreter and locked dependencies:

```bash
uv sync --all-groups
uv run pytest
uv run ruff check .
uv run mypy
```

The default non-secret configuration is in `configs/default.toml`. Documented overrides are `CLUELATTICE_ENV`, `CLUELATTICE_LOG_LEVEL`, and `CLUELATTICE_DATA_DIR`; see `.env.example`. ClueLattice does not automatically load `.env` files.

After obtaining authorization and placing the labeled file under the ignored `data/raw/` tree, run:

```bash
uv run python scripts/ingest_iot23.py \
  --input data/raw/iot23/CTU-IoT-Malware-Capture-34-1/bro/conn.log.labeled \
  --output-dir data/processed/iot23_capture_34_1 \
  --ingested-at 2026-09-21T00:00:00Z
```

The command writes `events.parquet`, `quality_report.json`, and `dataset_manifest.json`. It never downloads pcaps or malware binaries.

The real CTU-13 validation command is reproducible after placing the authoritative Scenario 11
`.binetflow` file at the recorded raw path:

```bash
uv run python scripts/ingest_ctu13.py \
  --input data/raw/ctu13/CTU-Malware-Capture-Botnet-52/capture20110818-2.binetflow \
  --output-dir data/processed/ctu13_scenario_11 \
  --ingested-at 2026-09-21T01:00:00Z \
  --report-generated-at 2026-09-21T01:00:00Z \
  --raw-reference data/raw/ctu13/CTU-Malware-Capture-Botnet-52/capture20110818-2.binetflow
```

This command consumes only labeled bidirectional text flows. The adapter preserves CTU-13 source
labels and scenario identity but does not turn them into ClueLattice detection or incident claims.

## Research Question

> Can a provenance-first, multi-model security system combine deterministic, supervised, anomaly, temporal, and reference-backed evidence to generate trustworthy investigation recommendations while clearly separating observed facts from inference and enabling a junior reviewer to handle basic triage without eliminating expert escalation?

The project will compare deterministic rules, justified statistical/ML and anomaly specialists,
optional interpretable fusion, deterministic findings, independently frozen structured AI reviews,
and human-reviewed recommendations. It will measure each layer separately so that polished
explanations, model agreement, or alert aggregation cannot hide weak evidence.

## Intended System

```text
Versioned telemetry
    -> source adapter
    -> canonical event + validation
    -> Parquet/DuckDB storage
    -> rules + specialist detectors
    -> disagreement analysis -> optional fusion
    -> deterministic finding + evidence bundle
    -> claim verification + reference evidence
    -> independent LLM triage and adjudication
    -> tiered human review and recommendation
    -> evaluation and audit trail
```

The LLM is an advisory component. It cannot create source evidence, overwrite detector output, or become the final authority.

## Initial Scope

- A small, versioned IoT-23 subset for the first reproducible Zeek network-flow pipeline.
- Seven real CTU-13 bidirectional Argus-flow scenarios are locally recorded across ingestion and validation work; only licensed labeled text flows were acquired.
- The current stability study uses Scenarios 11 and 47 for training and Scenarios 5, 12, 4, and 10 for validation; Scenario 7 is the sealed final holdout and is not used for tuning or comparison.
- Controlled synthetic fixtures for schema and failure-path tests.
- Cowrie JSON events as the second heterogeneous source after the first pipeline works.
- DShield telemetry for later exploratory/generalization analysis, never as malicious ground truth.
- A local-first Python stack using Pydantic, PyArrow/Parquet, scikit-learn, Ruff, mypy, and pytest; DuckDB/Pandas remain approved future tools where justified.
- A minimal Streamlit review interface only after detection, evidence, and triage records exist.

## Evidence Contract

Every conclusion must be traceable to stable identifiers for source events, detector results, evidence items, prompts/models, and reviewer decisions. Weak evidence must allow an explicit `insufficient_evidence` outcome. Unsupported claims about malware, exploitation, compromise, persistence, intent, or exfiltration must be flagged rather than presented as facts.

## Documentation

- [Project charter](docs/project_charter.md) — objectives, scope, research questions, risks, milestones, design critique, and learning plan.
- [Architecture](docs/architecture.md) — system boundaries, data flow, canonical entities, and technology choices.
- [Datasets](docs/datasets.md) — source selection, provenance, acquisition, labeling, and leakage controls.
- [Threat model](docs/threat_model.md) — defensive boundary, assets, threats, and mitigations.
- [Methodology](docs/methodology.md) — hypotheses, evidence hierarchy, and research controls.
- [Features](docs/features.md) — Phase 3A feature definitions, missingness, rationale, and leakage review.
- [Evaluation](docs/evaluation.md) — detector/ML evaluation protocol and the bounded Phase 3 exploratory results.
- [Staged roadmap](docs/roadmap.md) — current evidence, next validation-only experiments, optional research, and deferrals.
- [Phase 3 detector-improvement diagnostic](docs/phase3_detector_improvement.md) — validation-only false-negative analysis, feature comparison, threshold trade-offs, and next steps.
- [Phase 3 detector-hardening report](docs/phase3_detector_hardening.md) — ablation, temporal-leakage, calibration, alert-volume, and frozen-policy evidence before final testing.
- [Phase 3 model-family benchmark](docs/phase3_model_family_benchmark.md) — validation-only specialist comparison, per-case disagreement, and complexity recommendation.
- [Phase 3 cross-scenario stability report](docs/phase3_model_stability.md) — score semantics, validation-derived operating points, per-scenario metrics, SVM coverage, and residual errors.
- [Phase 3 causal representation report](docs/phase3_causal_representation.md) — prior-only host/time features, corrected-reference comparison, residual coverage, and limitations.
- [Phase 3 causal-overlap report](docs/phase3_causal_overlap.md) — deterministic case categories, Scenario 10/51 subgroup distributions, narrower hypothesis, and limits.
- [Experiment registry](docs/experiment_registry.json) — tracked run declarations, checksums, configuration, and claim boundaries.
- [Results ledger](docs/results.md) — every claim the project makes, its evidence tier, the artifact backing it, and what it does not support. Machine-checked against the registry by `scripts/validate_results_ledger.py`; [raw ledger](docs/results_ledger.json).
- [Artifact manifest](docs/artifact_manifest.json) — digest, size, and shape of each registered evaluation artifact, so a regenerating party can confirm they produced the same bytes. Note that the artifacts themselves are not committed; see [Limitations](docs/limitations.md).
- [Agent orchestration and provenance protocol](docs/agent_orchestration.md) — issue lifecycle, local trace linkage, escalation, and lesson promotion boundaries.
- [Versioned solution knowledge](docs/solution_knowledge.json) — validated reusable lessons only; issue and trace history remains in its original systems.
- [Limitations](docs/limitations.md) — current and expected validity constraints.
- [Resume evidence](docs/resume_evidence.md) — claimable work separated from planned work.
- [Phase 0 learning note](docs/learning_notes/phase_0.md) — concepts and interview explanation to understand before implementation.
- [Phase 1 learning note](docs/learning_notes/phase_1.md) — evidence identity, schema validation, manifests, configuration, and logging.
- [Phase 2B learning note](docs/learning_notes/phase_2b.md) — CTU-13 flow semantics, labels, scenario boundaries, and real-data validation evidence.
- [Phase 3 learning note](docs/learning_notes/phase_3.md) — features, rules, metrics, class imbalance, leakage, and scenario-aware evaluation.
- [Project memory](MEMORY.md) — durable architecture, workflow, and decision history.

## Roadmap

See the [staged roadmap](docs/roadmap.md). Phases 0–3 foundations and the bounded model-family
stability evidence are implemented and validated within their documented boundaries. The next
research step is either a scenario-held-out check of the bounded burst-density hypothesis or
deterministic finding aggregation if that check is not justified. Scenario 7 may be opened only
once, after the final policy is frozen.

## Safety Boundary

ClueLattice must remain defensive. Testing is limited to offline datasets, synthetic fixtures, localhost, isolated containers, controlled environments, or explicitly authorized defensive systems. It will not scan unowned systems, generate exploit payloads, automate credential attacks, or expose vulnerable services publicly.

## Portfolio Integrity

Nothing here is presented as production use, security impact, deployment scale, or operational
detection capability. The bounded validation results that do exist are recorded in the
[results ledger](docs/results.md) with their scope limits attached, and
[resume evidence](docs/resume_evidence.md) separates what was built from what is planned.
