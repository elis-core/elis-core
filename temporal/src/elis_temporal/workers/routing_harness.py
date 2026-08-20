"""Minimal client-side capability-gated dispatch harness.

Composes capability preflight with real Temporal dispatch: checks
capability admission FIRST, and only calls into the real Temporal
Workflow/Activity (and therefore only ever reaches Hermes/LLM execution) if
the verdict is ALLOW. If WAITING_FOR_CAPABILITY, returns immediately without
starting any Workflow.

Deliberately NOT Workflow code -- check_capability_preflight() performs
real IO (an AF_UNIX socket connect probe), which must never run inside
deterministic Workflow code. This harness is the minimum T1 composition
proving capability rejection happens strictly before any Hermes/LLM
invocation; a full implementer/preflight/validator Workflow primitive with
durable PO gates remains T2 scope, not attempted here.
"""

from __future__ import annotations

from typing import Optional

from temporalio.client import Client

from elis_temporal.activities.types import RunAgentActivityInput
from elis_temporal.capabilities.preflight import check_capability_preflight
from elis_temporal.profiles.routing import PROFILE_ROUTES
from elis_temporal.workflows.routing_workflow import RoutingWorkflow


async def dispatch_with_capability_gate(
    client: Client,
    profile: str,
    activity_input: RunAgentActivityInput,
    *,
    proposed_action: Optional[str] = None,
    po_approved: bool = False,
    workflow_id: Optional[str] = None,
    execution_timeout: Optional[float] = None,
) -> dict:
    route = PROFILE_ROUTES[profile]
    verdict = check_capability_preflight(
        profile,
        required_capabilities=route.capability_classes,
        proposed_action=proposed_action,
        po_approved=po_approved,
    )
    if verdict.decision != "ALLOW":
        return {
            "status": "blocked",
            "capability_verdict": verdict.to_dict(),
            "hermes_invoked": False,
        }

    handle = await client.start_workflow(
        RoutingWorkflow.run,
        activity_input,
        id=workflow_id or f"routing-{profile}-{activity_input.execution_id}",
        task_queue=route.task_queue,
    )
    if execution_timeout is not None:
        import asyncio

        result = await asyncio.wait_for(handle.result(), timeout=execution_timeout)
    else:
        result = await handle.result()
    result["hermes_invoked"] = True
    return result
