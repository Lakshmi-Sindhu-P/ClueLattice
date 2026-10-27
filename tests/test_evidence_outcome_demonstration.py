"""Executable three-class evidence demonstration (P0.2) — executed, not quoted.

The results ledger can say `REFUTED` or `UNKNOWN` as static text; that proves nothing about whether
the code actually produces and polices those outcome classes. This file runs the real runner
(`scripts/demonstrate_evidence_outcomes.py`) at process boundaries — spine demo CLI, ledger
validator CLI, the adversarial falsification suite, the triage E2E node — and pins:

1. every leg met its expectation on genuine execution;
2. two consecutive runs produce the identical `record_sha256` (the record is deterministic);
3. **the non-vacuity catch-test**: when the forger is flipped to emit a valid fixture, the known-bad
   leg observes acceptance instead of refusal, `expectations_met` turns false, and `main` exits
   non-zero — so this demonstration cannot pass while the validators stop catching forgeries.
"""

from __future__ import annotations

from pathlib import Path

from scripts.demonstrate_evidence_outcomes import demonstrate, main


def test_all_three_outcome_classes_are_produced_by_execution(tmp_path: Path) -> None:
    record = demonstrate(tmp_path / "run1")

    assert record["expectations_met"] is True, record
    assert set(record["legs"]) == {"known_good", "known_bad", "insufficient_evidence"}

    known_good = record["legs"]["known_good"]
    assert known_good["as_expected"] is True
    assert known_good["spine_demo"]["exit_code"] == 0
    assert known_good["spine_demo"]["deterministic_output"] is True
    assert known_good["spine_demo"]["output_sha256"], "a digest must be observed, not assumed"
    assert known_good["genuine_ledger"]["exit_code"] == 0

    known_bad = record["legs"]["known_bad"]
    assert known_bad["as_expected"] is True
    # Both known-bad fixtures were caught at the CLI boundary, with the right violation kind.
    assert known_bad["forged_value_ledger"]["exit_code"] == 1
    assert known_bad["forged_value_ledger"]["violation_kind"] == "mismatch"
    assert known_bad["nonexistent_reference_ledger"]["exit_code"] == 1
    assert known_bad["nonexistent_reference_ledger"]["violation_kind"] == "does not resolve"
    # Every forgery in the adversarial suite is refused by the code it attacks.
    assert known_bad["falsification_suite"]["exit_code"] == 0

    insufficient = record["legs"]["insufficient_evidence"]
    assert insufficient["as_expected"] is True
    assert insufficient["triage_e2e_node"]["exit_code"] == 0
    assert insufficient["abstention_claim_verifies"] is True
    assert insufficient["unknown_status_ledger"]["exit_code"] == 0


def test_two_consecutive_runs_produce_an_identical_record_digest(tmp_path: Path) -> None:
    first = demonstrate(tmp_path / "run1")
    second = demonstrate(tmp_path / "run2")
    assert first["record_sha256"] == second["record_sha256"]


def test_the_catch_test_forger_flip_fails_the_known_bad_leg(tmp_path: Path) -> None:
    """Non-vacuity: a forger that emits a valid fixture must break the demonstration.

    If the ledger validator ever stopped catching forged evidence, this flip would be
    indistinguishable from the honest run — so the demonstration's own expectation must be
    observed to fail here.
    """

    record = demonstrate(tmp_path / "flipped", forge_valid=True)
    assert record["forge_valid"] is True
    assert record["expectations_met"] is False
    forged = record["legs"]["known_bad"]["forged_value_ledger"]
    assert forged["as_expected"] is False
    assert forged["exit_code"] == 0, "the valid fixture was accepted — as it should be"
    assert record["legs"]["known_bad"]["as_expected"] is False


def test_main_exit_codes_at_the_entry_point(tmp_path: Path) -> None:
    out_ok = tmp_path / "ok.json"
    assert main(["--workdir", str(tmp_path / "ok"), "--output", str(out_ok)]) == 0
    assert '"expectations_met": true' in out_ok.read_text(encoding="utf-8")

    out_bad = tmp_path / "bad.json"
    assert (
        main(["--workdir", str(tmp_path / "bad"), "--output", str(out_bad), "--forge-valid"]) == 1
    )
    assert '"expectations_met": false' in out_bad.read_text(encoding="utf-8")
