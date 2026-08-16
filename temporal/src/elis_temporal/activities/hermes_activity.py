"""Temporal Activity wrapper around the Hermes Adapter.

This is where non-determinism (subprocess execution, real Hermes/LLM calls)
legitimately lives -- never inside Workflow code (see
workflows/routing_workflow.py, which references this Activity only by its
registered string name, never by importing this module).
"""

from __future__ import annotations

from temporalio import activity

from elis_temporal.activities.types import RunAgentActivityInput
from elis_temporal.adapter.hermes.adapter import AgentResult, run_agent

ACTIVITY_NAME = "run_agent_activity"


@activity.defn(name=ACTIVITY_NAME)
def run_agent_activity(inp: RunAgentActivityInput) -> dict:
    result: AgentResult = run_agent(
        profile=inp.profile,
        execution_id=inp.execution_id,
        instructions=inp.instructions,
        input_artifacts=inp.input_artifacts,
        required_capabilities=inp.required_capabilities,
        execution_context=inp.execution_context,
        correlation_id=inp.correlation_id,
        timeout_seconds=inp.timeout_seconds,
    )
    return result.to_dict()
