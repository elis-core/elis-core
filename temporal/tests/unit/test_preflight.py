from __future__ import annotations

import json

from elis_temporal.policies.preflight import run_deterministic_preflight


def test_completed_with_result_passes():
    verdict = run_deterministic_preflight({"status": "completed", "structured_result": "some output"})
    assert verdict.passed is True
    assert verdict.reasons == ()


def test_non_completed_status_fails():
    verdict = run_deterministic_preflight({"status": "failed", "structured_result": "x"})
    assert verdict.passed is False
    assert any("expected 'completed'" in r for r in verdict.reasons)


def test_empty_structured_result_fails():
    verdict = run_deterministic_preflight({"status": "completed", "structured_result": ""})
    assert verdict.passed is False


def test_required_keys_enforced_when_specified():
    verdict = run_deterministic_preflight(
        {"status": "completed", "structured_result": json.dumps({"foo": "bar"})},
        required_result_keys=("verdict",),
    )
    assert verdict.passed is False


def test_required_keys_pass_when_present():
    verdict = run_deterministic_preflight(
        {"status": "completed", "structured_result": json.dumps({"verdict": "PASS"})},
        required_result_keys=("verdict",),
    )
    assert verdict.passed is True
