from __future__ import annotations

from elis_temporal.policies.failure_taxonomy import (
    NON_RETRYABLE_CATEGORIES,
    classify_agent_result,
    default_hermes_activity_retry_policy,
    is_invalid_structured_result,
)


def _result(**overrides):
    base = {
        "status": "failed",
        "structured_result": None,
        "failure_class": None,
        "usage": {},
        "capability_result": None,
    }
    base.update(overrides)
    return base


def test_completed_is_successful_non_retryable():
    c = classify_agent_result(_result(status="completed", failure_class=None))
    assert c.category == "SUCCESSFUL_SUBSTANTIVE_RESULT"
    assert c.retryable is False


def test_timeout_is_retryable():
    """(test ledger item 15, part A) a transient timeout must classify
    retryable so Temporal's Activity retry actually engages."""
    c = classify_agent_result(_result(status="timeout", failure_class="timeout"))
    assert c.category == "TIMEOUT"
    assert c.retryable is True


def test_rate_limit_stderr_is_retryable():
    """(test ledger item 15, part B / item 16 precursor)."""
    c = classify_agent_result(
        _result(
            status="failed",
            failure_class="hermes_exit_1",
            usage={"stderr_tail": "Error: rate limit exceeded, HTTP 429"},
        )
    )
    assert c.category == "RATE_LIMIT_OR_TRANSIENT_UPSTREAM"
    assert c.retryable is True


def test_connection_reset_is_transient_provider_failure():
    c = classify_agent_result(
        _result(status="failed", failure_class="hermes_exit_1", usage={"stderr_tail": "connection reset by peer"})
    )
    assert c.category == "TRANSIENT_PROVIDER_FAILURE"
    assert c.retryable is True


def test_missing_binary_is_non_retryable_operator_required():
    """(test ledger item 18 precursor) local config defect must never
    blind-retry."""
    c = classify_agent_result(_result(status="failed", failure_class="hermes_binary_not_found"))
    assert c.category == "MISSING_HERMES_BINARY_OR_CONFIG_DEFECT"
    assert c.retryable is False


def test_unrecognized_exit_failure_defaults_non_retryable():
    """No blind retry loop against an unrecognized failure shape."""
    c = classify_agent_result(
        _result(status="failed", failure_class="hermes_exit_2", usage={"stderr_tail": "some unexplained crash"})
    )
    assert c.category == "UNCLASSIFIED_HERMES_FAILURE"
    assert c.retryable is False


def test_authorization_denied_from_capability_result_non_retryable():
    """(test ledger item 18, authorization denial) a capability_result
    that recorded a denial must classify as policy denial, not a Hermes
    execution failure, and must never retry."""
    c = classify_agent_result(
        _result(
            status="failed",
            failure_class="hermes_exit_1",
            capability_result={"checked": True, "allowed": False, "reasons": ["denied"]},
        )
    )
    assert c.category == "AUTHORIZATION_DENIED"
    assert c.retryable is False


def test_completed_status_wins_even_with_stale_capability_result():
    """A completed run with a passing capability_result stays a success --
    guards against the capability_result branch accidentally shadowing the
    completed-status fast path."""
    c = classify_agent_result(
        _result(status="completed", capability_result={"checked": True, "allowed": True, "reasons": []})
    )
    assert c.category == "SUCCESSFUL_SUBSTANTIVE_RESULT"


def test_default_retry_policy_is_bounded_and_lists_all_non_retryable_categories():
    policy = default_hermes_activity_retry_policy()
    assert policy.maximum_attempts > 0  # never Temporal's unbounded default (0 = infinite)
    assert set(policy.non_retryable_error_types) == set(NON_RETRYABLE_CATEGORIES)
    # retryable categories must NOT appear in the non-retryable list
    assert "TRANSIENT_PROVIDER_FAILURE" not in policy.non_retryable_error_types
    assert "RATE_LIMIT_OR_TRANSIENT_UPSTREAM" not in policy.non_retryable_error_types
    assert "TIMEOUT" not in policy.non_retryable_error_types


def test_invalid_structured_result_detects_non_json():
    assert is_invalid_structured_result("this is just prose, not json") is True


def test_invalid_structured_result_detects_missing_required_key():
    import json

    assert is_invalid_structured_result(json.dumps({"foo": "bar"}), required_keys=("verdict",)) is True


def test_valid_structured_result_with_required_key_passes():
    import json

    assert is_invalid_structured_result(json.dumps({"verdict": "PASS"}), required_keys=("verdict",)) is False


def test_empty_structured_result_is_invalid():
    assert is_invalid_structured_result(None) is True
    assert is_invalid_structured_result("") is True
