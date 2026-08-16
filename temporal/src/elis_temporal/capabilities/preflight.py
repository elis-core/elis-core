"""Capability-preflight admission gate.

Runs BEFORE any expensive Hermes/LLM Activity is dispatched. Returns ALLOW
or WAITING_FOR_CAPABILITY (never a crash) per plan v2.1 §9/§11.

This is deliberately a thin, honest check, not a full capability
vocabulary/ACL system — building that now would risk exactly the
"competing mechanism" the plan (§17) and the prior Hermes P2 session both
warned against, since Option-A is what will eventually define real
credential-provider availability for elis-github. What IS implemented:
the negative checks the plan explicitly requires regardless of Option-A's
final shape (no personal credential fallback, no unauthorized main push,
no merge without PO, no root capability for ordinary profiles), plus a
generic "does the profile's routing table claim this capability class at
all" check.
"""

from __future__ import annotations

import dataclasses
import os
from typing import Optional

from elis_temporal.profiles.routing import PROFILE_ROUTES

# Capability classes that must NEVER be satisfied by a personal/individual
# credential, regardless of profile. This directly encodes the standing
# platform rule already recorded for this session: personal `gh auth`
# (e.g. an individual GitHub login) must never be used for ELIS repo
# pushes/PRs, only the elis-github App identity is sanctioned.
FORBIDDEN_PERSONAL_CREDENTIAL_ENV_MARKERS = (
    "GH_TOKEN",  # a personal `gh` CLI token in the calling environment
    "GITHUB_TOKEN",  # generic personal PAT pattern
)


@dataclasses.dataclass(frozen=True)
class CapabilityAdmissionVerdict:
    decision: str  # "ALLOW" | "WAITING_FOR_CAPABILITY"
    profile: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


class UnknownProfileError(ValueError):
    pass


def check_capability_preflight(
    profile: str,
    required_capabilities: tuple[str, ...],
    *,
    proposed_action: Optional[str] = None,
    po_approved: bool = False,
    env: Optional[dict] = None,
) -> CapabilityAdmissionVerdict:
    route = PROFILE_ROUTES.get(profile)
    if route is None:
        raise UnknownProfileError(f"{profile!r} is not a routed ELIS profile")

    env = env if env is not None else os.environ
    reasons: list[str] = []

    # 1. Every required capability must be one the profile's routing table
    #    actually claims — an ordinary profile must never be granted a
    #    capability class it isn't configured for (e.g. no root capability
    #    for ordinary profiles).
    for cap in required_capabilities:
        if cap not in route.capability_classes:
            reasons.append(
                f"capability {cap!r} not in {profile!r}'s allowed capability_classes "
                f"{route.capability_classes!r}"
            )

    # 2. No personal credential fallback, ever, for any profile — this is
    #    checked regardless of which capabilities were requested, because a
    #    leaked/ambient personal token in the environment is exactly the
    #    incident class this exists to prevent (matches the `rochasamurai`
    #    push-credential incident already on record for Option-A/t_5d9a121f).
    for marker in FORBIDDEN_PERSONAL_CREDENTIAL_ENV_MARKERS:
        if env.get(marker):
            reasons.append(
                f"forbidden personal-credential marker {marker!r} present in "
                f"environment — personal/unapproved credential fallback is never permitted"
            )

    # 3. protected-branch push / repo administration / secrets changes are
    #    always prohibited regardless of profile, full stop, not just for
    #    elis-github.
    if proposed_action in ("protected_branch_push", "repo_administration", "secrets_change"):
        reasons.append(f"{proposed_action!r} is never permitted through this preflight, no exceptions")

    # 4. merge requires explicit PO approval, always.
    if proposed_action == "pr_merge" and not po_approved:
        reasons.append("pr_merge requires explicit PO approval (po_approved=True) and none was recorded")

    # 5. host_root_operation is only ever a PACKET-producing action, never a
    #    direct apply, for any profile including elis-supervisor.
    if proposed_action == "host_root_operation_direct_apply":
        reasons.append(
            "direct root application is never permitted through this preflight — "
            "only host_root_operation_PACKET_ONLY (produce a packet for PO/Supervisor)"
        )

    decision = "ALLOW" if not reasons else "WAITING_FOR_CAPABILITY"
    return CapabilityAdmissionVerdict(decision=decision, profile=profile, reasons=tuple(reasons))
