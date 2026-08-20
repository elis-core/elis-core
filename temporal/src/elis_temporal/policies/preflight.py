"""Deterministic completeness preflight (T2, directive section 9).

Pure/deterministic by construction (dict inspection only, no IO) -- unlike
capabilities/preflight.py (which does a real socket probe and therefore
must run in an Activity), this preflight is safe to call directly from
Workflow code, which is exactly what workflows/gated_pipeline_workflow.py
does. It deliberately does NOT replicate what a real ELIS PM preflight does
today (git/evidence/artifact inspection, per this project's memory of the
TEMPORAL-I1 T0/T1 gate history) -- that is genuinely IO-bound and
application-specific, out of scope for a generic, reusable T2 primitive.
This is the structural-completeness half only: did the implementer Activity
actually produce a "completed" result with the shape a validator can
meaningfully act on. It is what stands between "the implementer Activity
returned successfully" and "the validator gets invoked at all" -- see the
module docstring on gated_pipeline_workflow.py for why that gap is the
whole point of a separate preflight step.
"""

from __future__ import annotations

import dataclasses

from elis_temporal.policies.failure_taxonomy import is_invalid_structured_result


@dataclasses.dataclass(frozen=True)
class PreflightVerdict:
    passed: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def run_deterministic_preflight(
    implementer_result: dict,
    *,
    required_result_keys: tuple[str, ...] = (),
) -> PreflightVerdict:
    reasons: list[str] = []

    status = implementer_result.get("status")
    if status != "completed":
        reasons.append(f"implementer status={status!r}, expected 'completed' -- preflight cannot pass on a non-completed result")

    structured = implementer_result.get("structured_result")
    if required_result_keys and is_invalid_structured_result(structured, required_keys=required_result_keys):
        reasons.append(
            f"implementer structured_result failed structural completeness check "
            f"(required keys {required_result_keys!r} not all present in parseable JSON)"
        )
    elif not structured:
        reasons.append("implementer structured_result is empty -- nothing for a validator to act on")

    return PreflightVerdict(passed=not reasons, reasons=tuple(reasons))
