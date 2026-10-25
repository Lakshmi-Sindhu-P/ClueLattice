"""LLM triage layer: input isolation, assessment admission, and deterministic adjudication."""

from cluelattice.triage.agreement import compare_assessments
from cluelattice.triage.assessment import AssessmentOutcome, build_assessment
from cluelattice.triage.snapshot import (
    SNAPSHOT_FIELDS,
    bundle_evidence_ids,
    canonical_snapshot_json,
    input_snapshot,
    snapshot_digest,
)

__all__ = [
    "SNAPSHOT_FIELDS",
    "AssessmentOutcome",
    "build_assessment",
    "bundle_evidence_ids",
    "canonical_snapshot_json",
    "compare_assessments",
    "input_snapshot",
    "snapshot_digest",
]
