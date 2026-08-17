from __future__ import annotations

from typing import Optional

import pytest

from elis_temporal.idempotency.side_effect import (
    SideEffectConflictError,
    SideEffectOperation,
    apply_idempotent_side_effect,
)


class FakeGitHubBranchTarget:
    """Test fixture only -- see side_effect.py's module docstring: a real
    GitHub target is explicitly T3/T4 scope, directive section 15 forbids
    mutating production GitHub in T2. Models a "create branch at sha" op,
    keyed by operation_id, simulating a real remote's persistent state."""

    def __init__(self) -> None:
        self._by_operation_id: dict[str, dict] = {}
        self.write_call_count = 0

    def read(self, operation_id: str) -> Optional[dict]:
        return self._by_operation_id.get(operation_id)

    def write(self, operation: SideEffectOperation) -> dict:
        self.write_call_count += 1
        state = dict(operation.desired_state)
        self._by_operation_id[operation.operation_id] = state
        return state


class AckLostGitHubBranchTarget(FakeGitHubBranchTarget):
    """Simulates the exact "ambiguous external mutation" scenario (test
    ledger item 19): the write genuinely happens upstream, but the
    acknowledgment the caller was waiting on is lost -- from the caller's
    perspective the first attempt looked like a failure, so it retries.
    Models this by having `write()` succeed (mutating real state) but the
    FIRST caller never sees a normal return (simulated by the test calling
    write via the target directly, bypassing apply_idempotent_side_effect,
    then having a retry go through the real orchestration function)."""


def test_first_apply_writes_and_verifies():
    target = FakeGitHubBranchTarget()
    op = SideEffectOperation(
        operation_id="op-1", workflow_id="wf-1", target="github", desired_state={"branch": "feature-x", "sha": "abc123"}
    )
    outcome = apply_idempotent_side_effect(op, target)
    assert outcome.applied is True
    assert outcome.reconciled is False
    assert target.write_call_count == 1


def test_retry_after_lost_acknowledgment_reconciles_without_duplicate_write():
    """(test ledger item 19, the core case) The upstream write genuinely
    happened once already (simulating a lost ack) -- retrying the SAME
    operation_id must reconcile against the existing state, not write
    again."""
    target = AckLostGitHubBranchTarget()
    op = SideEffectOperation(
        operation_id="op-lost-ack", workflow_id="wf-1", target="github", desired_state={"branch": "feature-y", "sha": "def456"}
    )

    # Simulate: the original attempt's write genuinely succeeded upstream,
    # but its acknowledgment never reached the caller (a real network/
    # process failure mode) -- model this by writing directly via the
    # target, bypassing the orchestration function entirely (as if a prior
    # `apply_idempotent_side_effect` call's process crashed AFTER write()
    # returned but BEFORE this function could return to its own caller).
    target.write(op)
    assert target.write_call_count == 1

    # The caller, having seen what looked like a failure/timeout, retries
    # with the SAME operation_id.
    outcome = apply_idempotent_side_effect(op, target)

    assert outcome.reconciled is True
    assert outcome.applied is False  # no NEW write happened
    assert target.write_call_count == 1  # still exactly one real write -- no duplicate


def test_repeated_retries_never_duplicate():
    target = FakeGitHubBranchTarget()
    op = SideEffectOperation(operation_id="op-multi", workflow_id="wf-1", target="github", desired_state={"branch": "b", "sha": "s"})
    first = apply_idempotent_side_effect(op, target)
    second = apply_idempotent_side_effect(op, target)
    third = apply_idempotent_side_effect(op, target)

    assert first.applied is True
    assert second.reconciled is True and third.reconciled is True
    assert target.write_call_count == 1


def test_divergent_existing_state_raises_conflict_not_silently_overwritten():
    target = FakeGitHubBranchTarget()
    op_a = SideEffectOperation(operation_id="op-conflict", workflow_id="wf-1", target="github", desired_state={"branch": "b", "sha": "sha-a"})
    apply_idempotent_side_effect(op_a, target)

    op_b = SideEffectOperation(operation_id="op-conflict", workflow_id="wf-1", target="github", desired_state={"branch": "b", "sha": "sha-b"})
    with pytest.raises(SideEffectConflictError):
        apply_idempotent_side_effect(op_b, target)

    # the original state must be untouched by the failed conflicting attempt
    assert target.read("op-conflict") == {"branch": "b", "sha": "sha-a"}


def test_distinct_operation_ids_never_collide():
    target = FakeGitHubBranchTarget()
    op1 = SideEffectOperation(operation_id="op-x", workflow_id="wf-1", target="github", desired_state={"branch": "x"})
    op2 = SideEffectOperation(operation_id="op-y", workflow_id="wf-1", target="github", desired_state={"branch": "y"})
    apply_idempotent_side_effect(op1, target)
    apply_idempotent_side_effect(op2, target)
    assert target.write_call_count == 2
    assert target.read("op-x") != target.read("op-y")


def test_read_after_write_failure_raises_conflict():
    class BrokenWriteTarget(FakeGitHubBranchTarget):
        def write(self, operation: SideEffectOperation) -> dict:
            self.write_call_count += 1
            # write "succeeds" per its own return, but never actually
            # persists -- simulates a partially-failed/ambiguous write
            return dict(operation.desired_state)

    target = BrokenWriteTarget()
    op = SideEffectOperation(operation_id="op-broken", workflow_id="wf-1", target="github", desired_state={"branch": "z"})
    with pytest.raises(SideEffectConflictError):
        apply_idempotent_side_effect(op, target)
