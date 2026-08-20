from __future__ import annotations

import pytest

from elis_temporal.provenance.model import InvalidProvenanceRecord, build_provenance_record


def test_valid_record():
    rec = build_provenance_record(
        workflow_id="ELIS/core/gated-pipeline/t_1",
        run_id="run-abc",
        evidence_class="validation",
        artifact_ref="/home/samurai/temporal/app/artifacts/foo.md",
        sha256="a" * 64,
    )
    assert rec.workflow_id == "ELIS/core/gated-pipeline/t_1"
    assert rec.sha256 == "a" * 64


def test_missing_workflow_id_rejected():
    with pytest.raises(InvalidProvenanceRecord):
        build_provenance_record(workflow_id="", run_id="run-abc", evidence_class="validation", artifact_ref="x")


def test_malformed_sha256_rejected():
    with pytest.raises(InvalidProvenanceRecord):
        build_provenance_record(
            workflow_id="wf-1", run_id="run-1", evidence_class="validation", artifact_ref="x", sha256="not-a-hash"
        )


def test_sha256_optional():
    rec = build_provenance_record(workflow_id="wf-1", run_id="run-1", evidence_class="implementation", artifact_ref="x")
    assert rec.sha256 is None
