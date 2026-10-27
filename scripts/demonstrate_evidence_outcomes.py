"""Executable three-class evidence demonstration: known-good, known-bad, insufficient-evidence.

Each leg runs the repository's implemented code at a real process boundary (CLI entries and the
actual test suite) and records the OBSERVED outcome. Nothing in the record is copied from the
results ledger or any other static claim — the point of this runner is that a reader can rerun one
command and watch the three outcome classes being produced by execution.

Legs:

* **known-good** — the offline spine demo runs twice (same ``--created-at``) and must exit 0 with
  byte-identical output; a genuine ledger fixture must pass ``validate_results_ledger
  --require-artifacts``.
* **known-bad** — a ledger whose evidence value was forged, and one citing a nonexistent artifact
  key, must both FAIL the same CLI (caught); the adversarial falsification suite
  (``tests/test_decision_falsification.py``) must pass, i.e. every forged structure in it is
  refused by the code it attacks.
* **insufficient-evidence** — the real triage E2E node must pass (the pipeline admits an
  ``INSUFFICIENT_EVIDENCE`` assessment as pending review), an abstention claim must verify as
  ``UNKNOWN_INSUFFICIENT_EVIDENCE``, and a ledger claim with status ``UNKNOWN`` must validate as a
  legitimate record rather than being coerced into good or bad.

Honest limits: the spine demo uses mechanical stub providers (its output carries a warning saying
so), and the ledger fixtures are synthetic artifacts built for this runner. The demonstration is
about the CODE paths producing and policing the three outcome classes, not about model quality and
not about the frozen experiment.

``--forge-valid`` flips the forger to emit a structurally valid fixture; the known-bad leg then
observes acceptance instead of refusal, ``expectations_met`` turns false, and the process exits
non-zero. That is the built-in catch-test proving this demonstration cannot pass vacuously.

Exit code: 0 iff every leg met its expectation. The record is deterministic — no timestamps, no
temporary paths — so two consecutive runs produce the same ``record_sha256``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

REPO_ROOT = Path(__file__).resolve().parents[1]
CREATED_AT = "2026-10-08T13:00:00+00:00"
ARTIFACT_REL = "data/eval/demo.json"
EXPERIMENT_ID = "exp:demonstration"

#: Fixed, so the abstention claim's id is stable across runs (record digest must not drift).
CLAIM_NAMESPACE = uuid5(NAMESPACE_URL, "https://github.com/Lakshmi-Sindhu-P/ClueLattice/demos/v1")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(argv: list[str], *, cwd: Path | None = None) -> tuple[int, str]:
    completed = subprocess.run(
        argv,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode, completed.stderr + completed.stdout


def _write_ledger_fixture(
    directory: Path, evidence_value: bool, *, cite_missing_key: bool
) -> tuple[Path, Path]:
    """Write artifact + registry + ledger; the evidence string is either genuine or forged."""

    directory.mkdir(parents=True, exist_ok=True)
    artifact = directory / ARTIFACT_REL
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(json.dumps({"headline": {"best": True}}), encoding="utf-8")

    registry = {
        "schema_version": "1.0.0",
        "runs": [
            {
                "experiment_id": EXPERIMENT_ID,
                "artifact_refs": [
                    {
                        "path": ARTIFACT_REL,
                        "digest": _sha256(artifact),
                        "kind": "artifact",
                        "tracked": False,
                    }
                ],
            }
        ],
    }
    if cite_missing_key:
        evidence = ["headline.absent = true"]
    else:
        evidence = [f"headline.best = {'true' if evidence_value else 'false'}"]

    ledger = {
        "schema_version": "1.0.0",
        "claims": [
            {
                "claim_id": "claim:demonstration",
                "statement": "The demonstration artifact records headline.best = true.",
                "claim_type": "DETERMINISTIC_DERIVATION",
                "status": "SUPPORTED",
                "experiment_ids": [EXPERIMENT_ID],
                "artifact_refs": [ARTIFACT_REL],
                "evidence": evidence,
                "scope_limit": "Synthetic fixture; see scripts/demonstrate_evidence_outcomes.py.",
            }
        ],
    }
    ledger_path = directory / "ledger.json"
    registry_path = directory / "registry.json"
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    return ledger_path, registry_path


def _validate_ledger_cli(ledger_path: Path, registry_path: Path, cwd: Path) -> tuple[int, str]:
    return _run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "validate_results_ledger.py"),
            str(ledger_path),
            "--registry",
            str(registry_path),
            "--require-artifacts",
        ],
        cwd=cwd,
    )


def _classify(code: int, output: str, *, wanted: int) -> dict[str, Any]:
    violation = None
    for marker in ("does not resolve", "mismatch", "ambiguous"):
        if marker in output:
            violation = marker
            break
    return {
        "exit_code": code,
        "as_expected": code == wanted,
        "violation_kind": violation,
    }


def _known_good(tmp: Path) -> dict[str, Any]:
    demo_a = tmp / "spine_a.json"
    demo_b = tmp / "spine_b.json"
    spine_args = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "run_offline_spine_demo.py"),
        "--created-at",
        CREATED_AT,
    ]
    code_a, out_a = _run([*spine_args, "--output", str(demo_a)])
    code_b, _ = _run([*spine_args, "--output", str(demo_b)])
    deterministic = (
        code_a == 0 and code_b == 0 and demo_a.is_file() and _sha256(demo_a) == _sha256(demo_b)
    )

    ledger_path, registry_path = _write_ledger_fixture(
        tmp / "genuine", True, cite_missing_key=False
    )
    code, _ = _validate_ledger_cli(ledger_path, registry_path, tmp / "genuine")

    return {
        "spine_demo": {
            "exit_code": code_a,
            "second_run_exit_code": code_b,
            "deterministic_output": deterministic,
            "output_sha256": _sha256(demo_a) if demo_a.is_file() else None,
            "stderr_note": out_a if code_a else None,
        },
        "genuine_ledger": _classify(code, "", wanted=0),
        "as_expected": (
            code_a == 0
            and code_b == 0
            and deterministic
            and code == 0
        ),
    }


def _known_bad(tmp: Path, *, forge_valid: bool) -> dict[str, Any]:
    forged_dir = tmp / "forged_value"
    ledger_path, registry_path = _write_ledger_fixture(
        forged_dir, evidence_value=forge_valid, cite_missing_key=False
    )
    code_forged, out_forged = _validate_ledger_cli(ledger_path, registry_path, forged_dir)

    missing_dir = tmp / "missing_key"
    ledger_path, registry_path = _write_ledger_fixture(missing_dir, True, cite_missing_key=True)
    code_missing, out_missing = _validate_ledger_cli(ledger_path, registry_path, missing_dir)

    suite_code, suite_out = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-o",
            "addopts=",
            "tests/test_decision_falsification.py",
        ],
        cwd=REPO_ROOT,
    )

    forged = _classify(code_forged, out_forged, wanted=1)
    missing = _classify(code_missing, out_missing, wanted=1)
    suite: dict[str, Any] = {"exit_code": suite_code, "as_expected": suite_code == 0}
    if suite_code != 0:
        suite["tail"] = suite_out[-800:]
    return {
        "forged_value_ledger": forged,
        "nonexistent_reference_ledger": missing,
        "falsification_suite": suite,
        "as_expected": forged["as_expected"] and missing["as_expected"] and suite["as_expected"],
    }


def _insufficient_evidence(tmp: Path) -> dict[str, Any]:
    # Real pipeline: the triage E2E node admits an insufficient-evidence assessment.
    node_code, node_out = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-o",
            "addopts=",
            "tests/test_triage.py::test_insufficient_evidence_is_admissible_end_to_end",
        ],
        cwd=REPO_ROOT,
    )

    # Claim taxonomy: an explicit abstention verifies and is not upgraded.
    from cluelattice.schemas.findings import Claim, ClaimType
    from cluelattice.verification import verify_claim

    abstention = Claim(
        claim_id=uuid5(CLAIM_NAMESPACE, "abstention"),
        claim_type=ClaimType.UNKNOWN_INSUFFICIENT_EVIDENCE,
        statement="Insufficient evidence to state anything stronger.",
        created_at=datetime(2026, 10, 8, 13, 0, tzinfo=UTC),
    )
    verification = verify_claim(abstention)
    abstention_ok = (
        verification.verified is True
        and verification.effective_type is ClaimType.UNKNOWN_INSUFFICIENT_EVIDENCE
    )

    # Ledger: status UNKNOWN is a legitimate record, not coerced into good or bad.
    unknown_dir = tmp / "unknown_status"
    unknown_dir.mkdir(parents=True, exist_ok=True)
    ledger = {
        "schema_version": "1.0.0",
        "claims": [
            {
                "claim_id": "claim:insufficient",
                "statement": "Nothing stronger than insufficient evidence is assertible here.",
                "claim_type": "UNKNOWN_INSUFFICIENT_EVIDENCE",
                "status": "UNKNOWN",
                "experiment_ids": [],
                "artifact_refs": [],
                "evidence": ["No artifact-backed assertion is made."],
                "scope_limit": "Synthetic fixture; see scripts/demonstrate_evidence_outcomes.py.",
            }
        ],
    }
    registry = {"schema_version": "1.0.0", "runs": []}
    ledger_path = unknown_dir / "ledger.json"
    registry_path = unknown_dir / "registry.json"
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    code, out = _validate_ledger_cli(ledger_path, registry_path, unknown_dir)
    unknown_ok = code == 0

    return {
        "triage_e2e_node": (
            {"exit_code": node_code, "as_expected": node_code == 0}
            | ({"tail": node_out[-800:]} if node_code != 0 else {})
        ),
        "abstention_claim_verifies": abstention_ok,
        "unknown_status_ledger": _classify(code, out, wanted=0),
        "as_expected": node_code == 0 and abstention_ok and unknown_ok,
    }


def demonstrate(tmp: Path, *, forge_valid: bool = False) -> dict[str, Any]:
    """Execute all three legs under ``tmp`` and return the deterministic record."""

    legs = {
        "known_good": _known_good(tmp),
        "known_bad": _known_bad(tmp, forge_valid=forge_valid),
        "insufficient_evidence": _insufficient_evidence(tmp),
    }
    expectations_met = all(leg["as_expected"] for leg in legs.values())
    record: dict[str, Any] = {
        "demonstration": "cluelattice-evidence-outcomes/v1",
        "forge_valid": forge_valid,
        "legs": legs,
        "expectations_met": expectations_met,
    }
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    record["record_sha256"] = hashlib.sha256(canonical).hexdigest()
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, help="write the JSON record here (stdout if omitted)"
    )
    parser.add_argument(
        "--forge-valid",
        action="store_true",
        help="forger emits a valid fixture; the known-bad leg must then fail its expectation",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=None,
        help="fixture directory (default: a fresh temp dir that is deleted afterwards)",
    )
    args = parser.parse_args(argv)

    import tempfile

    if args.workdir is not None:
        record = demonstrate(args.workdir, forge_valid=args.forge_valid)
        exit_code = 0 if record["expectations_met"] else 1
        text = json.dumps(record, indent=2, sort_keys=True) + "\n"
        if args.output is not None:
            args.output.write_text(text, encoding="utf-8")
        print(text, end="")
        return exit_code

    with tempfile.TemporaryDirectory(prefix="cluelattice-evidence-outcomes-") as directory:
        record = demonstrate(Path(directory), forge_valid=args.forge_valid)
        exit_code = 0 if record["expectations_met"] else 1
        text = json.dumps(record, indent=2, sort_keys=True) + "\n"
        if args.output is not None:
            args.output.write_text(text, encoding="utf-8")
        print(text, end="")
        return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
