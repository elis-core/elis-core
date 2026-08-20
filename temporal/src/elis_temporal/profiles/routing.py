"""Six-ELIS-profile Temporal Task Queue routing table.

Grounded in live `systemctl --user list-units` output taken 2026-08-16
during this implementation session — not assumed. See the "live_gateway"
field on each entry.

IMPORTANT — read before trusting this at face value:
ELIS GitHub has no persistent gateway service. It is dispatcher-invoked
per-task today (only `elis-a2a-github.service`, an A2A server, is
persistent). This is presumed deliberate (narrow, credential-isolated,
invoked-not-standing role) but was not independently confirmed against
governance docs in this session — flagged, not assumed.

`expected_security_principal` records what SHOULD be true once Option-A
(t_5d9a121f, still `blocked` as of this session) lands. It is NOT
enforced by gh-agentd today — this table is forward-looking policy
data for the execution-context-fidelity check in
`policies/execution_context.py`, not a claim that isolation is
currently live.
"""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class ProfileRoute:
    profile: str  # ELIS profile name, matches Hermes profile / HERMES_PROFILE value
    task_queue: str  # Temporal Task Queue name
    live_gateway: str  # actual systemd unit observed live, or "none (dispatcher-only)"
    expected_security_principal: str  # intended uid/systemd-unit identity, may not be enforced yet
    allowed_activity_classes: tuple[str, ...]
    prohibited_activity_classes: tuple[str, ...]
    concurrency_policy: str
    capability_classes: tuple[str, ...]


PROFILE_ROUTES: dict[str, ProfileRoute] = {
    "elis-ideas": ProfileRoute(
        profile="elis-ideas",
        task_queue="elis-ideas-queue",
        live_gateway="hermes-gateway-elis-ideas.service",
        expected_security_principal="uid(hermes-gateway-elis-ideas.service)",
        allowed_activity_classes=("cognitive_reasoning", "notification"),
        prohibited_activity_classes=("github_mutation", "host_root_operation", "credential_access"),
        concurrency_policy="unbounded",  # ideation is low-risk, no exclusivity requirement known
        capability_classes=(),
    ),
    "elis-pm": ProfileRoute(
        profile="elis-pm",
        task_queue="elis-pm-queue",
        live_gateway="hermes-gateway-elis-pm.service",
        expected_security_principal="uid(hermes-gateway-elis-pm.service)",
        allowed_activity_classes=("cognitive_reasoning", "orchestration_decision", "notification"),
        prohibited_activity_classes=(
            "github_mutation",
            "host_root_operation",
            "credential_access",
            "self_validation",
        ),
        concurrency_policy="one_active_run_per_profile_global",  # matches Hermes P2 b4767a9dd4's invariant
        capability_classes=("kanban_read", "kanban_write"),
    ),
    "elis-research": ProfileRoute(
        profile="elis-research",
        task_queue="elis-research-queue",
        live_gateway="hermes-gateway-elis-research.service",
        expected_security_principal="uid(hermes-gateway-elis-research.service)",
        allowed_activity_classes=("cognitive_reasoning", "research_domain_work", "notification"),
        prohibited_activity_classes=(
            "github_mutation",
            "host_root_operation",
            "credential_access",
            "self_validation",
        ),
        concurrency_policy="one_active_run_per_profile_global",
        capability_classes=("kanban_read", "kanban_write"),
    ),
    "elis-advisor": ProfileRoute(
        profile="elis-advisor",
        task_queue="elis-advisor-queue",
        live_gateway="hermes-gateway-elis-advisor.service",
        expected_security_principal="uid(hermes-gateway-elis-advisor.service)",
        allowed_activity_classes=("cognitive_reasoning", "independent_validation", "notification"),
        prohibited_activity_classes=(
            "github_mutation",
            "host_root_operation",
            "credential_access",
            "implementation_write",
            "self_validation",
        ),
        concurrency_policy="configurable_per_gate",  # plan explicitly allows non-global concurrency here
        capability_classes=("kanban_read",),
    ),
    "elis-supervisor": ProfileRoute(
        profile="elis-supervisor",
        task_queue="elis-supervisor-queue",
        live_gateway="hermes-gateway-elis-supervisor.service",
        expected_security_principal="uid(hermes-gateway-elis-supervisor.service)",
        allowed_activity_classes=(
            "cognitive_reasoning",
            "host_root_operation_PACKET_ONLY",  # produces packets; applying them is a separate PO-gated step
            "runtime_platform_change",
            "notification",
        ),
        prohibited_activity_classes=("github_mutation", "self_validation", "unauthorized_root_apply"),
        concurrency_policy="one_active_run_per_profile_global",
        capability_classes=("kanban_read", "kanban_write", "host_inspect"),
    ),
    "elis-github": ProfileRoute(
        profile="elis-github",
        task_queue="elis-github-queue",
        live_gateway="none (dispatcher-only; only elis-a2a-github.service is persistent)",
        expected_security_principal="uid 995 / hermes-gateway-elis-github.service (per gh-agentd design, NOT YET ENFORCED — Option-A blocked)",
        allowed_activity_classes=("feature_branch_push", "draft_pr_create", "pr_update", "read_back_verify"),
        prohibited_activity_classes=(
            "protected_branch_push",
            "pr_merge",
            "repo_administration",
            "secrets_change",
            "self_validation",
        ),
        concurrency_policy="one_active_run_per_profile_global",
        capability_classes=("github_app_credential",),  # per-profile, NOT per-board — see policies/execution_context.py docstring
    ),
}
