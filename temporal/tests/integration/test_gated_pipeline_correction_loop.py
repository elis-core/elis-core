"""Proves the "corrections return to implementation inside the same
logical Workflow" structural invariant (directive section 9) -- not part
of the mandatory 20-item test ledger, but a real structural feature this
T2 implementation built, so it gets a real test rather than shipping
unverified."""

from __future__ import annotations

import asyncio
import json
import uuid
from unittest.mock import patch

import pytest
from temporalio.client import Client

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
        correlation_id="correction-loop-test",
    )


@pytest.mark.asyncio
async def test_correction_signal_loops_back_to_implementer_same_workflow():
    """First validator verdict is FAIL -> workflow waits for a correction
    signal (same Workflow ID, no new start) -> after the signal, the
    implementer Activity runs again with the correction reason appended ->
    second validator verdict PASS -> proceeds to WAITING_FOR_PO."""
    client = await _connect_or_skip()
    call_log: list[tuple] = []

    def _side_effect(*, profile, instructions, **kwargs):
        call_log.append((profile, instructions))
        if profile == "elis-pm":
            return _completed(profile, f"implementation (instructions={instructions!r})")
        # validator: FAIL on first call, PASS on second
        val_calls = [c for c in call_log if c[0] == "elis-advisor"]
        if len(val_calls) == 1:
            return _completed(profile, json.dumps({"verdict": "FAIL", "reason": "needs more detail"}))
        return _completed(profile, json.dumps({"verdict": "PASS"}))

    with patch("elis_temporal.activities.hermes_activity.run_agent", side_effect=_side_effect):
        worker = build_worker_for_profile("elis-pm", client)
        async with worker:
            inp = GatedPipelineInput(
                implementer_profile="elis-pm",
                validator_profile="elis-advisor",
                implementer_instructions="implement something",
                validator_instructions="validate it",
                execution_id=f"correction-{uuid.uuid4().hex[:8]}",
                po_gate_id="gate-1",
                authorized_po_identities=("carlos",),
            )
            wf_id = f"ELIS/core/gated-pipeline/{uuid.uuid4().hex[:8]}"
            handle = await client.start_workflow(GatedPipelineWorkflow.run, inp, id=wf_id, task_queue="elis-pm-queue")

            for _ in range(50):
                stage = await handle.query(GatedPipelineWorkflow.stage)
                if stage == "waiting_for_correction":
                    break
                await asyncio.sleep(0.1)
            assert stage == "waiting_for_correction"

            await handle.signal(GatedPipelineWorkflow.request_correction, "please add more detail")

            for _ in range(50):
                stage = await handle.query(GatedPipelineWorkflow.stage)
                if stage == "waiting_for_po":
                    break
                await asyncio.sleep(0.1)
            assert stage == "waiting_for_po"

            approval = await handle.execute_update(GatedPipelineWorkflow.approve_gate, args=["gate-1", "carlos"])
            assert approval["approved"] is True

            result = await handle.result()

    assert result["stage"] == "po_approved"
    implementer_calls = [c for c in call_log if c[0] == "elis-pm"]
    assert len(implementer_calls) == 2  # genuinely re-invoked, not just re-read a cached result
    assert "CORRECTION REQUESTED: please add more detail" in implementer_calls[1][1]
    # SAME Workflow ID throughout -- this is a signal against the open run,
    # never a new Workflow start.
    desc = await handle.describe()
    assert desc.id == wf_id
