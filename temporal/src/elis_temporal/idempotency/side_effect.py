"""External side-effect idempotency framework (T2, directive section 15).

Reusable contract for any external mutation (GitHub, Discord, filesystem/
artifacts): operation_id, workflow_id, target, desired_state,
read_before_write, write, read_after_write, reconcile. The generic
orchestration (`apply_idempotent_side_effect`) is pure control flow -- the
actual IO lives entirely in a caller-supplied `SideEffectTarget`
implementation, so this module itself has zero side-effecting imports and
is safe to unit test deterministically against a fake target.

Central guarantee this proves (test ledger item 19 -- "ambiguous external
mutation reconciles without duplication"): if a write's acknowledgment is
lost (the operation may or may not have actually happened upstream) and the
same `operation_id` is retried, `read_before_write` must discover the prior
attempt's actual effect and `reconcile` instead of blindly writing again --
never a second, duplicate mutation for the same operation_id.

GitHub target implementations here are test fixtures/fakes only --
directive section 15 explicitly forbids mutating production GitHub in T2.
A real GitHub-backed `SideEffectTarget` (calling the sanctioned
elis-github/gh-agentd broker, per this platform's established publication
boundary) is T3/T4 production-integration scope, structurally ready to
slot in behind the same Protocol without touching
`apply_idempotent_side_effect` itself.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional, Protocol


@dataclasses.dataclass(frozen=True)
class SideEffectOperation:
    operation_id: str
    workflow_id: str
    target: str
    desired_state: dict[str, Any]

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class SideEffectOutcome:
    operation_id: str
    applied: bool  # True if a write genuinely happened THIS call (not reconciled from a prior one)
    reconciled: bool  # True if an existing prior effect was found and reused instead of writing again
    final_state: dict[str, Any]
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


class SideEffectTarget(Protocol):
    """Implemented per external system (GitHub, Discord, filesystem). All
    three methods are keyed by `operation_id`, not by any transient
    request/response artifact -- that is what makes reconciliation
    possible after an ambiguous (lost-acknowledgment) prior attempt."""

    def read(self, operation_id: str) -> Optional[dict]:
        """Return the current observed state for this operation_id, or
        None if no prior effect is observable."""
        ...  # pragma: no cover - protocol

    def write(self, operation: SideEffectOperation) -> dict:
        """Perform the actual mutation. Must be safe to call at most once
        per operation_id in the common case -- `apply_idempotent_side_effect`
        only calls this when `read()` found nothing, but a caller's target
        implementation should still defend against a genuine upstream
        duplicate (e.g. a real API's own idempotency-key support) where
        practical; that is target-specific and out of this module's scope."""
        ...  # pragma: no cover - protocol


class SideEffectConflictError(Exception):
    """Raised when read_after_write's observed state does not match
    desired_state and no reconciliation is possible -- a genuine defect,
    not a retry-safe condition."""


def apply_idempotent_side_effect(operation: SideEffectOperation, target: SideEffectTarget) -> SideEffectOutcome:
    # 1. read_before_write -- discover whether this exact operation_id
    #    already has an observable effect (this is what makes a retry after
    #    a lost acknowledgment safe: the retry finds the ORIGINAL attempt's
    #    real effect instead of blindly writing a second time).
    existing = target.read(operation.operation_id)
    if existing is not None:
        if _state_matches(existing, operation.desired_state):
            return SideEffectOutcome(
                operation_id=operation.operation_id,
                applied=False,
                reconciled=True,
                final_state=existing,
                reasons=("read_before_write found a prior effect matching desired_state -- reconciled, not re-written",),
            )
        raise SideEffectConflictError(
            f"operation_id {operation.operation_id!r} already has an observed effect "
            f"{existing!r} that does not match desired_state {operation.desired_state!r} -- "
            f"cannot silently overwrite a divergent prior result"
        )

    # 2. write -- no prior effect found, perform the real mutation.
    written = target.write(operation)

    # 3. read_after_write -- verify the mutation actually achieved the
    #    desired state, rather than trusting the write call's own return
    #    value blindly.
    confirmed = target.read(operation.operation_id)
    if confirmed is None or not _state_matches(confirmed, operation.desired_state):
        raise SideEffectConflictError(
            f"operation_id {operation.operation_id!r}: post-write verification did not confirm "
            f"desired_state {operation.desired_state!r} (observed {confirmed!r}) -- write may have "
            f"partially failed or been ambiguous"
        )

    return SideEffectOutcome(
        operation_id=operation.operation_id,
        applied=True,
        reconciled=False,
        final_state=confirmed,
        reasons=("write performed and read_after_write confirmed desired_state",),
    )


def _state_matches(observed: dict, desired: dict) -> bool:
    return all(observed.get(k) == v for k, v in desired.items())
