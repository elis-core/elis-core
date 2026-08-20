"""Capability-preflight admission gate.

Runs BEFORE any expensive Hermes/LLM Activity is dispatched. Returns ALLOW
or WAITING_FOR_CAPABILITY (never a crash) per plan v2.1 §9/§11.

CORRECTED (PO bounded T1 correction, this session): the original version of
this module only checked whether a capability was *declared* in a profile's
routing table, never whether the sanctioned execution path was *actually
reachable*. That produced a false ALLOW for
``elis-github`` + ``github_app_credential`` + ``po_approved=True`` even
though the real gh-agentd broker path is unreachable (Option-A / t_5d9a121f
still blocked) — a live security gap, not a formality.

Fixed by making every capability check pass through three explicit,
independently-inspectable conditions:

    declared    -- is the profile's routing table configured to use this
                   capability class at all?
    authorized  -- has policy/PO approved *this* proposed use of it right
                   now (e.g. po_approved for a merge)? Distinct from
                   *availability* — a merge can be PO-approved while the
                   underlying credential path is still unreachable.
    available   -- is the sanctioned execution path for this capability
                   *actually reachable from this process, right now*,
                   positively verified rather than assumed?

A capability is only ``executable`` (and thus eligible to contribute to an
ALLOW verdict) when all three are true. This module stays generic — it does
not hardcode "Option-A" or "gh-agentd" as concepts, only as the one
registered availability probe for the one capability class that currently
needs one (``github_app_credential``). Capability classes with no
registered probe (``kanban_read``, ``kanban_write``, ``host_inspect`` — all
local, not backed by an external credential broker in this project's scope)
default ``available=True``, keeping this a thin, honest check rather than a
full capability-vocabulary/ACL system (building that generally is out of
scope here — see the module-level warning in the previous revision, still
true).

The overall two-value ``decision`` field (``ALLOW`` / ``WAITING_FOR_CAPABILITY``)
is preserved for backward compatibility with existing callers; the granular
per-capability ``CapabilityConditions`` are additionally exposed on the
verdict so a caller (or Advisor) can see exactly which of the three
conditions failed, rather than only an opaque final verdict.
"""

from __future__ import annotations

import dataclasses
import os
import socket
from typing import Callable, Optional

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

# The sanctioned broker socket path for the elis-github GitHub App credential
# path (Option-A's target mechanism, t_5d9a121f). This module does not
# implement or alter gh-agentd in any way — it only attempts a plain AF_UNIX
# connect() as a positive reachability probe. A successful connect proves
# nothing about *authorization* (gh-agentd's own peer authentication is a
# separate, untouched concern) — it only proves the mechanism is online, so
# this preflight can stop conservatively assuming unavailability once
# Option-A actually lands. A failed connect (including PermissionError,
# ConnectionRefusedError, FileNotFoundError — all subclasses of OSError) is
# treated as "not available", which is the conservative, safe default.
GH_AGENTD_SOCKET_PATH = "/run/gh-agentd"


def _probe_gh_agentd_socket_reachable() -> bool:
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.settimeout(0.5)
            sock.connect(GH_AGENTD_SOCKET_PATH)
            return True
        finally:
            sock.close()
    except OSError:
        return False


# Registry of positive-availability probes, keyed by capability class. A
# capability with no registered probe here is treated as locally available
# (True) by default -- it is not backed by an external credential broker in
# this project's scope. Only capability classes that genuinely depend on an
# external, independently-operated sanctioned path get a real probe.
DEFAULT_AVAILABILITY_PROBES: dict[str, Callable[[], bool]] = {
    "github_app_credential": _probe_gh_agentd_socket_reachable,
}


@dataclasses.dataclass(frozen=True)
class CapabilityConditions:
    capability: str
    declared: bool
    authorized: bool
    available: bool

    @property
    def executable(self) -> bool:
        return self.declared and self.authorized and self.available

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["executable"] = self.executable
        return d


@dataclasses.dataclass(frozen=True)
class CapabilityAdmissionVerdict:
    decision: str  # "ALLOW" | "WAITING_FOR_CAPABILITY"
    profile: str
    reasons: tuple[str, ...]
    capability_conditions: tuple[CapabilityConditions, ...] = ()

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["capability_conditions"] = [c.to_dict() for c in self.capability_conditions]
        return d


class UnknownProfileError(ValueError):
    pass


def check_capability_preflight(
    profile: str,
    required_capabilities: tuple[str, ...],
    *,
    proposed_action: Optional[str] = None,
    po_approved: bool = False,
    env: Optional[dict] = None,
    availability_probes: Optional[dict[str, Callable[[], bool]]] = None,
) -> CapabilityAdmissionVerdict:
    """``availability_probes`` lets a caller (chiefly tests) override/extend
    the default probe registry for specific capability classes -- e.g. to
    deterministically exercise the "available=True" eligible path without
    depending on real host socket state, or to inject a hostile fake
    override that must still fail to defeat the authorization/declared
    checks. Production callers should omit this and get the real default
    registry.
    """
    route = PROFILE_ROUTES.get(profile)
    if route is None:
        raise UnknownProfileError(f"{profile!r} is not a routed ELIS profile")

    env = env if env is not None else os.environ
    probes = dict(DEFAULT_AVAILABILITY_PROBES)
    if availability_probes:
        probes.update(availability_probes)

    reasons: list[str] = []

    # ---- Action-level hard policy rules (apply regardless of which
    # capabilities were requested) — these determine the "authorized" half
    # for every requested capability in this call. ----
    action_authorized = True
    if proposed_action in ("protected_branch_push", "repo_administration", "secrets_change"):
        action_authorized = False
        reasons.append(f"{proposed_action!r} is never permitted through this preflight, no exceptions")
    if proposed_action == "pr_merge" and not po_approved:
        action_authorized = False
        reasons.append("pr_merge requires explicit PO approval (po_approved=True) and none was recorded")
    if proposed_action == "host_root_operation_direct_apply":
        action_authorized = False
        reasons.append(
            "direct root application is never permitted through this preflight — "
            "only host_root_operation_PACKET_ONLY (produce a packet for PO/Supervisor)"
        )

    # ---- Per-capability DECLARED / AUTHORIZED / AVAILABLE evaluation ----
    conditions: list[CapabilityConditions] = []
    for cap in required_capabilities:
        declared = cap in route.capability_classes
        if not declared:
            reasons.append(
                f"capability {cap!r} not in {profile!r}'s allowed capability_classes "
                f"{route.capability_classes!r} (declared=False)"
            )

        authorized = action_authorized

        probe = probes.get(cap)
        available = probe() if probe is not None else True
        if declared and authorized and not available:
            reasons.append(
                f"capability {cap!r} is declared and authorized for {profile!r} but its "
                f"sanctioned execution path is not currently reachable (available=False) — "
                f"waiting, not denied; re-checked on every call, no caching"
            )

        conditions.append(
            CapabilityConditions(capability=cap, declared=declared, authorized=authorized, available=available)
        )

    # ---- No personal credential fallback, ever, for any profile — checked
    # regardless of which capabilities were requested, and this check can
    # NEVER cause `available` to become True for any capability; it is a
    # wholly separate, additional rejection reason. ----
    for marker in FORBIDDEN_PERSONAL_CREDENTIAL_ENV_MARKERS:
        if env.get(marker):
            reasons.append(
                f"forbidden personal-credential marker {marker!r} present in "
                f"environment — personal/unapproved credential fallback is never permitted "
                f"and never substitutes for a genuinely available sanctioned path"
            )

    all_executable = all(c.executable for c in conditions)
    decision = "ALLOW" if (not reasons and all_executable) else "WAITING_FOR_CAPABILITY"

    return CapabilityAdmissionVerdict(
        decision=decision,
        profile=profile,
        reasons=tuple(reasons),
        capability_conditions=tuple(conditions),
    )
