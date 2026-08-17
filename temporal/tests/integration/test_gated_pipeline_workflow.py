"""Proves GatedPipelineWorkflow's structural invariants against the real
dev server -- test ledger items 3, 4, 8 (workflow-level half), 9, 10, 11, 12."""

from __future__ import annotations

import json
import uuid
from unittest.mock import patch

import pytest
from temporalio.client import Client, WorkflowFailureError, WorkflowUpdateFailedError
from temporalio.exceptions import ActivityError, ApplicationError

from elis_temporal.adapter.hermes.adapter import AgentResult, RuntimeIdentity
from elis_temporal.workers.worker import build_worker_for_profile
from elis_temporal.workflows.gated_pipeline_workflow import GatedPipelineInput, GatedPipelineWorkflow


async def _connect_or_skip() -> Client:
    try:
        return await Client.connect("127.0.0.1:7233", namespace="elis")
    except RuntimeError as exc:
        pytest.skip(f"Temporal dev server not reachable at 127.0.0.1:7233: {exc}")
        raise


def _identity(profile: str) -> RuntimeIdentity:
    return RuntimeIdentity(os_user="samurai", uid=1000, pid=0, hermes_profile_env=profile, cgroup_path=None, systemd_unit=None)


def _completed(profile: str, structured_result) -> AgentResult:
    return AgentResult(
        status="completed",
        structured_result=structured_result,
        evidence_refs=(),
        checkpoint=None,
        usage={"elapsed_seconds": 0.01},
        failure_class=None,
        runtime_identity=_identity(profile),
        capability_result=None,
        correlation_id="gated-pipeline-test",
    )


@pytest.mark.asyncio
async def test_preflight_failed_never_invokes_validator():
    """(test ledger item 9) implementer "completes" with an empty
    structured_result -> preflight fails -> validator Activity must
    provably never run."""
    client = await _connect_or_skip()
    call_log: list[str] = []

    def _side_effect(*, profile, **kwargs):
        call_log.append(profile)
        return _completed(profile, "")  # empty -- fails preflight

    with patch("elis_temporal.activities.hermes_activity.run_agent", side_effect=_side_effect):
        worker = build_worker_for_profile("elis-pm", client)
        async with worker:
            inp = GatedPipelineInput(
                implementer_profile="elis-pm",
                validator_profile="elis-advisor",
                implementer_instructions="implement something",
                validator_instructions="validate it",
                execution_id=f"preflight-fail-{uuid.uuid4().hex[:8]}",
                po_gate_id="gate-1",
                authorized_po_identities=("carlos",),
            )
            handle = await client.start_workflow(
                GatedPipelineWorkflow.run,
                inp,
                id=f"ELIS/core/gated-pipeline/{uuid.uuid4().hex[:8]}",
                task_queue="elis-pm-queue",
            )
            result = await handle.result()

    assert result["stage"] == "preflight_failed"
    assert result["preflight_result"]["passed"] is False
    assert call_log == ["elis-pm"]  # validator ("elis-advisor") never invoked


@pytest.mark.asyncio
async def test_preflight_pass_invokes_validator_and_invalid_result_stage():
    """(test ledger item 10 + item 4) A structurally-complete implementer
    result DOES trigger the validator; a validator that returns non-JSON
    prose (not the required {"verdict": ...} shape) lands in its own
    distinct stage, never silently coerced to PASS/FAIL."""
    client = await _connect_or_skip()
    call_log: list[str] = []

    def _side_effect(*, profile, **kwargs):
        call_log.append(profile)
        if profile == "elis-pm":
            return _completed(profile, "here is my real implementation output")
        return _completed(profile, "looks good to me")  # not JSON -- invalid structured result

    with patch("elis_temporal.activities.hermes_activity.run_agent", side_effect=_side_effect):
        worker = build_worker_for_profile("elis-pm", client)
        async with worker:
            inp = GatedPipelineInput(
                implementer_profile="elis-pm",
                validator_profile="elis-advisor",
                implementer_instructions="implement something",
                validator_instructions="validate it",
                execution_id=f"invalid-result-{uuid.uuid4().hex[:8]}",
                po_gate_id="gate-1",
                authorized_po_identities=("carlos",),
            )
            handle = await client.start_workflow(
                GatedPipelineWorkflow.run,
                inp,
                id=f"ELIS/core/gated-pipeline/{uuid.uuid4().hex[:8]}",
                task_queue="elis-pm-queue",
            )
            result = await handle.result()

    assert call_log == ["elis-pm", "elis-advisor"]  # preflight passed, validator WAS invoked
    assert result["stage"] == "invalid_validator_result"


@pytest.mark.asyncio
async def test_full_flow_waits_for_po_then_wrong_gate_and_unauthorized_rejected_then_approves():
    """(test ledger items 11 + 12) After a PASS verdict the workflow must
    genuinely sit open/WAITING_FOR_PO (not auto-complete); an approval
    aimed at the wrong gate_id or from an unauthorized identity must be
    rejected without touching the real gate; only the correct approval
    completes it."""
    client = await _connect_or_skip()

    def _side_effect(*, profile, **kwargs):
        if profile == "elis-pm":
            return _completed(profile, "real implementation output")
        return _completed(profile, json.dumps({"verdict": "PASS"}))

    with patch("elis_temporal.activities.hermes_activity.run_agent", side_effect=_side_effect):
        worker = build_worker_for_profile("elis-pm", client)
        async with worker:
            inp = GatedPipelineInput(
                implementer_profile="elis-pm",
                validator_profile="elis-advisor",
                implementer_instructions="implement something",
                validator_instructions="validate it",
                execution_id=f"po-gate-{uuid.uuid4().hex[:8]}",
                po_gate_id="the-real-gate",
                authorized_po_identities=("carlos",),
            )
            wf_id = f"ELIS/core/gated-pipeline/{uuid.uuid4().hex[:8]}"
            handle = await client.start_workflow(
                GatedPipelineWorkflow.run, inp, id=wf_id, task_queue="elis-pm-queue"
            )

            # Give the workflow time to reach waiting_for_po, then confirm via query.
            import asyncio

            for _ in range(50):
                stage = await handle.query(GatedPipelineWorkflow.stage)
                if stage == "waiting_for_po":
                    break
                await asyncio.sleep(0.1)
            assert stage == "waiting_for_po"

            desc = await handle.describe()
            assert desc.status.name == "RUNNING"  # genuinely still open, not auto-completed

            # wrong gate_id rejected
            with pytest.raises(WorkflowUpdateFailedError) as exc_info:
                await handle.execute_update(GatedPipelineWorkflow.approve_gate, args=["wrong-gate", "carlos"])
            assert "WRONG_GATE" in str(exc_info.value.cause)

            # unauthorized identity rejected
            with pytest.raises(WorkflowUpdateFailedError) as exc_info:
                await handle.execute_update(GatedPipelineWorkflow.approve_gate, args=["the-real-gate", "someone-else"])
            assert "UNAUTHORIZED_ACTOR" in str(exc_info.value.cause)

            # still open after both rejections
            desc = await handle.describe()
            assert desc.status.name == "RUNNING"

            # correct approval, fired twice concurrently (a genuine duplicate-
            # approval race) -- both must succeed, neither may error, and this
            # must not double-process the gate. Fired via gather rather than
            # sequentially because a single approval unblocks run()'s
            # wait_condition almost immediately, completing the Workflow
            # before a second, later RPC could ever reach it.
            import asyncio as _asyncio

            approval, dup = await _asyncio.gather(
                handle.execute_update(GatedPipelineWorkflow.approve_gate, args=["the-real-gate", "carlos"]),
                handle.execute_update(GatedPipelineWorkflow.approve_gate, args=["the-real-gate", "carlos"]),
            )
            assert approval["approved"] is True
            assert dup["approved"] is True
            # exactly one of the two observed the "first" transition
            assert sorted([approval["already_approved"], dup["already_approved"]]) == [False, True]

            result = await handle.result()

    assert result["stage"] == "po_approved"
    assert result["po_approval"] == {"gate_id": "the-real-gate", "po_identity": "carlos"}


@pytest.mark.asyncio
async def test_self_validation_rejected_at_workflow_start():
    """(test ledger item 8, workflow-level half) implementer_profile ==
    validator_profile must fail the Workflow immediately, before either
    Activity is ever scheduled."""
    client = await _connect_or_skip()
    call_log: list[str] = []

    def _side_effect(*, profile, **kwargs):
        call_log.append(profile)
        return _completed(profile, "should never be reached")

    with patch("elis_temporal.activities.hermes_activity.run_agent", side_effect=_side_effect):
        worker = build_worker_for_profile("elis-pm", client)
        async with worker:
            inp = GatedPipelineInput(
                implementer_profile="elis-pm",
                validator_profile="elis-pm",  # same as implementer -- must reject
                implementer_instructions="x",
                validator_instructions="y",
                execution_id=f"self-val-{uuid.uuid4().hex[:8]}",
                po_gate_id="gate-1",
                authorized_po_identities=("carlos",),
            )
            handle = await client.start_workflow(
                GatedPipelineWorkflow.run,
                inp,
                id=f"ELIS/core/gated-pipeline/{uuid.uuid4().hex[:8]}",
                task_queue="elis-pm-queue",
            )
            with pytest.raises(WorkflowFailureError) as exc_info:
                await handle.result()

    assert call_log == []  # no Activity ever ran
    assert isinstance(exc_info.value.cause, ApplicationError)
    assert exc_info.value.cause.type == "SELF_VALIDATION_REJECTED"
