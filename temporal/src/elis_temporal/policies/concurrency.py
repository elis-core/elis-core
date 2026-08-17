"""Profile concurrency policy (T2, directive section 11).

Two concurrency policies exist per profiles/routing.py's
``ProfileRoute.concurrency_policy`` field, already populated in T1:

  "unbounded"                         -- elis-ideas only; no exclusivity.
  "one_active_run_per_profile_global" -- elis-pm/elis-research/
                                          elis-supervisor/elis-github;
                                          matches the Hermes P2 remediation
                                          branch's `ONE_ACTIVE_RUN_PER_PROFILE`
                                          invariant (`b4767a9dd4`), reimplemented
                                          here with a genuinely Temporal-native
                                          mechanism instead of a filesystem
                                          flock.
  "configurable_per_gate"             -- elis-advisor; T2 does not build a
                                          gate-scoped variant (no concrete
                                          gate-level exclusivity requirement
                                          was specified) -- DEFERRED, treated
                                          as unbounded for now, flagged in
                                          the T2 packet.

Mechanism, deliberately NOT a custom lock table or filesystem primitive
(directive: "Do NOT assume Workflow ID uniqueness implements profile
exclusivity... prefer native Worker/Task Queue/concurrency mechanisms where
sufficient"): one long-lived singleton Workflow per profile
(ProfileExclusivityWorkflow, workflow ID
``ELIS/platform/profile-lock/<profile>``) acting as a mutex via a
`@workflow.update` handler that blocks the caller
(`workflow.wait_condition`) until it becomes the holder. This is Temporal's
own documented "entity workflow as a mutex" pattern -- the concurrency
control lives in ordinary Workflow state + Update, not a separate
datastore, so it durably survives worker restarts the same way any other
Workflow state does.
"""

from __future__ import annotations

from elis_temporal.policies.workflow_identity import build_semantic_workflow_id
from elis_temporal.profiles.routing import PROFILE_ROUTES

GLOBAL_EXCLUSIVITY_POLICY = "one_active_run_per_profile_global"
UNBOUNDED_POLICY = "unbounded"
CONFIGURABLE_PER_GATE_POLICY = "configurable_per_gate"  # DEFERRED, see module docstring


def requires_global_exclusivity(profile: str) -> bool:
    route = PROFILE_ROUTES[profile]
    return route.concurrency_policy == GLOBAL_EXCLUSIVITY_POLICY


def profile_lock_workflow_id(profile: str) -> str:
    return build_semantic_workflow_id("platform", "profile-lock", profile)
