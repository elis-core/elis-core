"""Minimal single-Activity pass-through Workflow.

Proves the six-profile Task-Queue routing mechanism works end-to-end
through real Temporal -- this is NOT an orchestration engine. It exists
only to establish T1 routing per plan v2.1 correction #2. Deliberately NOT
implemented here (T2 scope): semantic Workflow-ID policy beyond what this
minimal harness needs, a decomposition engine, the
implementer/preflight/validator Workflow primitive, a durable PO gate, or
any broad concurrency framework.

References the Activity by its registered string name only
(``run_agent_activity``) rather than importing activities/hermes_activity.py
directly -- that module imports the Hermes Adapter, which imports
subprocess/socket/os. Keeping those imports out of this file is what keeps
this Workflow's determinism boundary structurally enforced, not just
documented.
"""

from __future__ import annotations

from datetime import timedelta

from temporalio import workflow

from elis_temporal.activities.types import RunAgentActivityInput
from elis_temporal.policies.failure_taxonomy import default_hermes_activity_retry_policy


@workflow.defn(name="RoutingWorkflow")
class RoutingWorkflow:
    @workflow.run
    async def run(self, inp: RunAgentActivityInput) -> dict:
        # T2 compatible extension (directive section 20): attach the bounded
        # Hermes-failure-taxonomy retry policy so real Hermes failures
        # actually engage Temporal's native Activity retry instead of
        # silently returning as a "successful" result -- see
        # policies/failure_taxonomy.py and
        # docs/ELIS-TEMPORAL-FAILURE-RETRY-POLICY.md.
        return await workflow.execute_activity(
            "run_agent_activity",
            inp,
            start_to_close_timeout=timedelta(seconds=inp.timeout_seconds + 30),
            retry_policy=default_hermes_activity_retry_policy(),
        )
