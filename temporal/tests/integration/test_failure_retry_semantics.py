"""Proves the T2 failure-taxonomy -> Temporal retry mapping actually
engages against the real dev server -- not asserted from the unit-level
classification alone. Test-ledger items 15/16/18 (17/19 are covered
elsewhere: 17 in test_gated_pipeline_workflow.py's WAITING_FOR_PO tests,
19 in test_side_effect_idempotency.py)."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from temporalio.client import Client, WorkflowFailureError
from temporalio.exceptions import ActivityError, ApplicationError

from elis_temporal.activities.types import RunAgentActivityInput
from elis_temporal.adapter.hermes.adapter import AgentResult, CapabilityResult, RuntimeIdentity
from elis_temporal.workers.worker import build_worker_for_profile
from elis_temporal.workflows.routing_workflow import RoutingWorkflow


async def _connect_or_skip() -> Client:
    try:
        return await Client.connect("127.0.0.1:7233", namespace="elis")
    except RuntimeError as exc:
        pytest.skip(f"Temporal dev server not reachable at 127.0.0.1:7233: {exc}")
        raise


def _identity() -> RuntimeIdentity:
    return RuntimeIdentity(os_user="samurai", uid=1000, pid=0, hermes_profile_env="elis-ideas", cgroup_path=None, systemd_unit=None)


def _transient_then_success_result(call_count: dict):
    def _side_effect(**kwargs):
        call_count["n"] = call_count.get("n", 0) + 1
        if call_count["n"] < 3:
            return AgentResult(
                status="failed",
                structured_result=None,
                evidence_refs=(),
                checkpoint=None,
                usage={"stderr_tail": "503 service temporarily unavailable", "returncode": 1},
                failure_class="hermes_exit_1",
                runtime_identity=_identity(),
                capability_result=None,
                correlation_id="retry-test",
            )
        return AgentResult(
            status="completed",
            structured_result="finally succeeded",
            evidence_refs=(),
            checkpoint=None,
            usage={"elapsed_seconds": 0.01},
            failure_class=None,
            runtime_identity=_identity(),
            capability_result=None,
            correlation_id="retry-test",
        )

    return _side_effect


@pytest.mark.asyncio
async def test_transient_failure_retries_then_succeeds():
    """(test ledger item 15) A transient Hermes failure must actually
    trigger Temporal's native Activity retry -- proven by failing twice
    then succeeding, and observing the workflow completes successfully
    with the eventual result, having genuinely retried (call_count == 3)."""
    client = await _connect_or_skip()
    call_count: dict = {}

    with patch("elis_temporal.activities.hermes_activity.run_agent", side_effect=_transient_then_success_result(call_count)):
        worker = build_worker_for_profile("elis-ideas", client)
        async with worker:
            inp = RunAgentActivityInput(
                profile="elis-ideas",
                execution_id=f"retry-transient-{uuid.uuid4().hex[:8]}",
                instructions="unused-fake",
                timeout_seconds=5,
            )
            handle = await client.start_workflow(
                RoutingWorkflow.run,
                inp,
                id=f"ELIS/core/routing-retry-test/{uuid.uuid4().hex[:8]}",
                task_queue="elis-ideas-queue",
            )
            result = await handle.result()

    assert result["structured_result"] == "finally succeeded"
    assert call_count["n"] == 3  # genuinely retried twice before succeeding


@pytest.mark.asyncio
async def test_missing_binary_never_retries():
    """(test ledger item 18, permanent-config-defect half) a non-retryable
    classification must fail the Workflow after exactly ONE Activity
    attempt -- no blind retry loop against a local config defect."""
    client = await _connect_or_skip()
    call_count: dict = {}

    def _always_missing_binary(**kwargs):
        call_count["n"] = call_count.get("n", 0) + 1
        return AgentResult(
            status="failed",
            structured_result=None,
            evidence_refs=(),
            checkpoint=None,
            usage={"elapsed_seconds": 0.0},
            failure_class="hermes_binary_not_found",
            runtime_identity=_identity(),
            capability_result=None,
            correlation_id="no-retry-test",
        )

    with patch("elis_temporal.activities.hermes_activity.run_agent", side_effect=_always_missing_binary):
        worker = build_worker_for_profile("elis-ideas", client)
        async with worker:
            inp = RunAgentActivityInput(
                profile="elis-ideas",
                execution_id=f"no-retry-{uuid.uuid4().hex[:8]}",
                instructions="unused-fake",
                timeout_seconds=5,
            )
            handle = await client.start_workflow(
                RoutingWorkflow.run,
                inp,
                id=f"ELIS/core/routing-retry-test/{uuid.uuid4().hex[:8]}",
                task_queue="elis-ideas-queue",
            )
            with pytest.raises(WorkflowFailureError) as exc_info:
                await handle.result()

    assert call_count["n"] == 1  # exactly one attempt, no retry storm
    activity_error = exc_info.value.cause
    assert isinstance(activity_error, ActivityError)
    cause = activity_error.cause
    assert isinstance(cause, ApplicationError)
    assert cause.type == "MISSING_HERMES_BINARY_OR_CONFIG_DEFECT"
    assert cause.non_retryable is True


@pytest.mark.asyncio
async def test_authorization_denied_never_retries():
    """(test ledger item 18, authorization-denial half)."""
    client = await _connect_or_skip()
    call_count: dict = {}

    def _always_denied(**kwargs):
        call_count["n"] = call_count.get("n", 0) + 1
        return AgentResult(
            status="failed",
            structured_result=None,
            evidence_refs=(),
            checkpoint=None,
            usage={"elapsed_seconds": 0.0},
            failure_class="hermes_exit_1",
            runtime_identity=_identity(),
            capability_result=CapabilityResult(checked=True, allowed=False, reasons=("policy denial",)),
            correlation_id="denied-test",
        )

    with patch("elis_temporal.activities.hermes_activity.run_agent", side_effect=_always_denied):
        worker = build_worker_for_profile("elis-ideas", client)
        async with worker:
            inp = RunAgentActivityInput(
                profile="elis-ideas",
                execution_id=f"denied-{uuid.uuid4().hex[:8]}",
                instructions="unused-fake",
                timeout_seconds=5,
            )
            handle = await client.start_workflow(
                RoutingWorkflow.run,
                inp,
                id=f"ELIS/core/routing-retry-test/{uuid.uuid4().hex[:8]}",
                task_queue="elis-ideas-queue",
            )
            with pytest.raises(WorkflowFailureError) as exc_info:
                await handle.result()

    assert call_count["n"] == 1
    activity_error = exc_info.value.cause
    assert isinstance(activity_error, ActivityError)
    cause = activity_error.cause
    assert isinstance(cause, ApplicationError)
    assert cause.type == "AUTHORIZATION_DENIED"
