"""Hermes failure taxonomy -> Temporal Activity retry mapping (T2, mandatory
per directive section 12).

The problem this closes: T1's ``run_agent_activity`` always returned
``AgentResult.to_dict()`` successfully, even when ``AgentResult.status`` was
"failed"/"timeout" -- because the Adapter is deliberately never-raising (see
adapter.py's docstring), Temporal's own exception-driven Activity retry
never engaged for ANY Hermes-level failure. That was correct T1 scope (the
Adapter's job is to observe and report honestly, not decide retry policy)
but left a real gap flagged explicitly in this project's T1 packet.

This module is the missing policy layer: it classifies an already-produced
``AgentResult``/dict into exactly one of the categories below and says
whether/how Temporal should retry. It does NOT change the Adapter -- the
Adapter still never raises. The classification + the raise-if-appropriate
step happens one layer up, in activities/hermes_activity.py, which is
allowed to translate a structured non-exception result into a Temporal
``ApplicationError`` because THAT boundary (Activity, not Adapter) is where
retry policy belongs.

Categories (directive section 12), each mapped to retryable/non-retryable:

  SUCCESSFUL_SUBSTANTIVE_RESULT  -- normal Activity result, no error raised
  TRANSIENT_PROVIDER_FAILURE     -- retryable Temporal Activity failure
  RATE_LIMIT_OR_TRANSIENT_UPSTREAM -- retryable, bounded RetryPolicy
  TIMEOUT                        -- retryable (transient by default here --
                                     see docstring on classify_agent_result)
  AUTHORIZATION_DENIED           -- non-retryable policy result
  INVALID_STRUCTURED_LLM_RESULT  -- non-retryable validation failure
                                     (regeneration is an explicit, separate
                                     policy decision, not built here -- see
                                     docs/ELIS-TEMPORAL-FAILURE-RETRY-POLICY.md,
                                     "Deferred" section)
  MISSING_HERMES_BINARY_OR_CONFIG_DEFECT -- non-retryable, operator-required,
                                     no blind retry loop
  UNCLASSIFIED_HERMES_FAILURE    -- non-retryable by default (conservative:
                                     an unrecognized failure shape must never
                                     silently become an infinite retry loop)

WAITING_FOR_CAPABILITY and WAITING_FOR_PO are deliberately NOT categories
here -- they are Workflow/policy states that never reach this Activity at
all (capability preflight runs before any Workflow start;
WAITING_FOR_PO is a durable `workflow.wait_condition`, not an Activity
outcome) -- see docs/ELIS-TEMPORAL-FAILURE-RETRY-POLICY.md for why an
Activity-retry storm structurally cannot happen for either state.
"""

from __future__ import annotations

import dataclasses
from datetime import timedelta
from typing import Optional

from temporalio.common import RetryPolicy

# Substring markers checked against the Adapter's captured stderr tail to
# distinguish a genuinely transient provider/network condition from an
# unknown failure. Conservative and explicit rather than clever: only these
# known markers earn a retryable classification; everything else defaults
# to UNCLASSIFIED_HERMES_FAILURE (non-retryable), per the directive's "do
# not keep every Hermes failure as a successful Activity result merely
# because AgentResult can encode it" instruction, applied symmetrically to
# "do not blindly retry either."
_TRANSIENT_MARKERS = (
    "rate limit",
    "429",
    "econnreset",
    "econnrefused",
    "connection reset",
    "connection refused",
    "temporarily unavailable",
    "503",
    "502",
    "gateway timeout",
    "network",
    "interrupted during api call",
)


@dataclasses.dataclass(frozen=True)
class FailureClassification:
    category: str
    retryable: bool
    reason: str

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def classify_agent_result(result: dict) -> FailureClassification:
    """``result`` is an ``AgentResult.to_dict()``-shaped mapping (as
    produced by adapter.run_agent / activities.hermes_activity). Pure
    function, no IO -- safe to unit test deterministically and safe to call
    from either Activity or (if ever needed) Workflow code."""
    status = result.get("status")
    failure_class = result.get("failure_class")
    usage = result.get("usage") or {}
    stderr_tail = str(usage.get("stderr_tail") or "").lower()
    capability_result = result.get("capability_result")

    if status == "completed":
        return FailureClassification(
            category="SUCCESSFUL_SUBSTANTIVE_RESULT", retryable=False, reason="hermes exited 0"
        )

    if capability_result is not None and capability_result.get("checked") and not capability_result.get("allowed"):
        return FailureClassification(
            category="AUTHORIZATION_DENIED",
            retryable=False,
            reason="capability_result.allowed=False -- policy denial, not a Hermes execution failure",
        )

    if status == "timeout":
        return FailureClassification(
            category="TIMEOUT",
            retryable=True,
            reason="hermes -z exceeded its timeout_seconds -- treated as transient by default; a "
            "caller with evidence a specific timeout is structural (not transient) should set a "
            "tight RetryPolicy.maximum_attempts rather than relying on this default",
        )

    if failure_class == "hermes_binary_not_found":
        return FailureClassification(
            category="MISSING_HERMES_BINARY_OR_CONFIG_DEFECT",
            retryable=False,
            reason="hermes binary not found on PATH -- a local environment defect, not a transient "
            "condition; retrying blindly would never succeed and would mask the real problem",
        )

    if failure_class and failure_class.startswith("hermes_exit_"):
        if any(marker in stderr_tail for marker in _TRANSIENT_MARKERS):
            hit = next(marker for marker in _TRANSIENT_MARKERS if marker in stderr_tail)
            category = "RATE_LIMIT_OR_TRANSIENT_UPSTREAM" if hit in ("rate limit", "429") else "TRANSIENT_PROVIDER_FAILURE"
            return FailureClassification(
                category=category,
                retryable=True,
                reason=f"stderr tail matched transient marker {hit!r}: {stderr_tail[-200:]!r}",
            )
        return FailureClassification(
            category="UNCLASSIFIED_HERMES_FAILURE",
            retryable=False,
            reason=f"{failure_class} with no recognized transient marker in stderr tail -- "
            f"defaulting non-retryable to avoid a blind retry loop against an unrecognized failure shape",
        )

    return FailureClassification(
        category="UNCLASSIFIED_HERMES_FAILURE",
        retryable=False,
        reason=f"unrecognized status/failure_class combination (status={status!r}, "
        f"failure_class={failure_class!r}) -- defaulting non-retryable",
    )


def is_invalid_structured_result(structured_result: Optional[str], *, required_keys: tuple[str, ...] = ()) -> bool:
    """Used by callers (chiefly the gated-pipeline validator step) to check
    whether a "completed" AgentResult's structured_result is actually a
    well-formed, parseable structured decision rather than free prose --
    "completed" only means Hermes exited 0, it says nothing about whether
    the output is the specific structured schema a caller needed."""
    if not structured_result:
        return True
    import json

    try:
        parsed = json.loads(structured_result)
    except (ValueError, TypeError):
        return True
    if not isinstance(parsed, dict):
        return True
    return any(key not in parsed for key in required_keys)


# Every category this taxonomy can classify as non-retryable. This is the
# actual mechanism that makes retry/non-retry decisions -- NOT a per-category
# RetryPolicy chosen ahead of time (impossible: the category is only known
# AFTER the Activity fails, from inside the Activity itself). Instead, one
# bounded RetryPolicy is attached at Workflow-level `execute_activity(...)`
# call sites, with `non_retryable_error_types` naming every category below.
# Temporal's own retry logic then does the right thing natively: an
# ApplicationError whose `type` matches one of these names stops retrying
# immediately (regardless of attempts remaining); any other type retries up
# to `maximum_attempts`. This is the correct, idiomatic mapping of
# ApplicationError.type -> RetryPolicy.non_retryable_error_types per the
# installed temporalio 1.31.0 API (confirmed directly against
# temporalio.exceptions.ApplicationError / temporalio.common.RetryPolicy
# signatures -- the Developer Skill was not active this session, see
# docs/TEMPORAL-I1-IMPLEMENTATION-REFERENCES.md).
NON_RETRYABLE_CATEGORIES: tuple[str, ...] = (
    "AUTHORIZATION_DENIED",
    "INVALID_STRUCTURED_LLM_RESULT",
    "MISSING_HERMES_BINARY_OR_CONFIG_DEFECT",
    "UNCLASSIFIED_HERMES_FAILURE",
)


def default_hermes_activity_retry_policy() -> RetryPolicy:
    """Single bounded RetryPolicy for `run_agent_activity` dispatch.
    Never Temporal's unbounded default (omitting retry_policy means
    "retry forever" server-side) -- matching this project's established
    preference for bounded/fail-safe behavior over hangs (see the Hermes P2
    15s-lock-timeout precedent this session's ProfileExclusivityWorkflow
    also follows)."""
    return RetryPolicy(
        initial_interval=timedelta(seconds=2),
        backoff_coefficient=2.0,
        maximum_interval=timedelta(seconds=30),
        maximum_attempts=4,
        non_retryable_error_types=list(NON_RETRYABLE_CATEGORIES),
    )
