"""Temporal Activity wrapper around the Hermes Adapter.

This is where non-determinism (subprocess execution, real Hermes/LLM calls)
legitimately lives -- never inside Workflow code (see
workflows/routing_workflow.py, which references this Activity only by its
registered string name, never by importing this module).

T2 addition: the Adapter itself never raises (by design, see
adapter.py's docstring) -- this Activity is the layer that translates a
structured-but-failed AgentResult into a Temporal ApplicationError via
policies/failure_taxonomy.py, which is what makes Temporal's native
Activity-retry mechanism (RetryPolicy, non_retryable_error_types) actually
engage for real Hermes failures. Before T2 this never happened -- every
Hermes failure mode silently became a "successful" Activity result, which
is the exact gap this project's T1 packet flagged and left open. A
"completed" AgentResult (hermes exited 0) still returns the plain dict, as
before -- only genuinely failed/timed-out/denied results now raise.
"""

from __future__ import annotations

from temporalio import activity
from temporalio.exceptions import ApplicationError

from elis_temporal.activities.types import RunAgentActivityInput
from elis_temporal.adapter.hermes.adapter import AgentResult, run_agent
from elis_temporal.policies.failure_taxonomy import classify_agent_result

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
    result_dict = result.to_dict()
    classification = classify_agent_result(result_dict)
    if classification.category == "SUCCESSFUL_SUBSTANTIVE_RESULT":
        return result_dict

    raise ApplicationError(
        f"run_agent_activity classified as {classification.category}: {classification.reason}",
        result_dict,
        type=classification.category,
        non_retryable=not classification.retryable,
    )
