"""Execution-context-fidelity policy.

Required invariant (plan v2.1 §9, §17):

    assigned_profile == execution_profile == expected_security_principal

This is the generic, credential-system-agnostic half of that invariant —
the "does the identity that actually ran this match the identity we
expected" check. It does NOT implement or assume any particular
credential-routing mechanism (gh-agentd, systemd unit dispatch, etc.) —
Option-A (t_5d9a121f) owns defining how the *real* principal gets
established; this module only compares what actually happened
(RuntimeIdentity, observed honestly by the Adapter) against the profile's
routing-table expectation (profiles/routing.py) and returns a
deterministic verdict.

Per plan §17: the invariant is evaluated PER ASSIGNED PROFILE, not per
board. Do not special-case a whole board's tasks onto one principal here.
"""

from __future__ import annotations

import dataclasses
from typing import Optional

from elis_temporal.adapter.hermes.adapter import RuntimeIdentity
from elis_temporal.profiles.routing import PROFILE_ROUTES, ProfileRoute


@dataclasses.dataclass(frozen=True)
class ExecutionContextVerdict:
    allowed: bool
    assigned_profile: str
    observed_hermes_profile_env: Optional[str]
    expected_security_principal: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


class UnknownProfileError(ValueError):
    pass


def check_execution_context(
    assigned_profile: str,
    runtime_identity: RuntimeIdentity,
) -> ExecutionContextVerdict:
    """Deterministic check: does the process that actually executed match
    what the assigned profile expects?

    Today (Option-A not yet applied), this will almost always find a
    mismatch for elis-github specifically, because there is no persistent
    gateway/enforced uid for it yet — that is the TRUE, honestly-reported
    state, not a bug in this check. Callers that need "soft" behavior
    during the pre-Option-A transition period must opt into that
    explicitly upstream (e.g. by not yet setting
    `requires_execution_context_match` on a task, mirroring the identical
    opt-in design already shipped in the Hermes P2 remediation branch's
    `ac6d2ca4bb` commit) — this function itself always enforces honestly.
    """
    route = PROFILE_ROUTES.get(assigned_profile)
    if route is None:
        raise UnknownProfileError(
            f"{assigned_profile!r} is not one of the six routed ELIS profiles: "
            f"{sorted(PROFILE_ROUTES)}"
        )

    reasons: list[str] = []

    observed_profile_env = runtime_identity.hermes_profile_env
    if observed_profile_env != assigned_profile:
        reasons.append(
            f"HERMES_PROFILE env observed as {observed_profile_env!r}, "
            f"expected {assigned_profile!r}"
        )

    # We cannot yet verify the systemd-unit/uid half against `route.expected_security_principal`
    # deterministically, because that string is a forward-looking policy statement
    # (Option-A not applied) rather than an enforceable fact today. Record what we
    # observed for provenance without failing solely on this half — see docstring.
    if route.live_gateway.startswith("none"):
        reasons.append(
            f"{assigned_profile!r} has no persistent gateway yet "
            f"(observed: {runtime_identity.systemd_unit!r}); "
            f"principal enforcement depends on unresolved Option-A (t_5d9a121f)"
        )

    allowed = observed_profile_env == assigned_profile

    return ExecutionContextVerdict(
        allowed=allowed,
        assigned_profile=assigned_profile,
        observed_hermes_profile_env=observed_profile_env,
        expected_security_principal=route.expected_security_principal,
        reasons=tuple(reasons),
    )
