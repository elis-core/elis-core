"""Proves the notification Activity actually delivers (against the real
dev server) and, critically, never invokes Hermes -- test ledger item 20.
Also proves a delivery failure never propagates to fail the calling
Workflow (directive section 14)."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from temporalio.client import Client

from elis_temporal.activities.notification_activity import set_default_sink
from elis_temporal.policies.notification import FailingNotificationSink, InMemoryNotificationSink, NullNotificationSink
from elis_temporal.workers.worker import build_worker_for_profile


async def _connect_or_skip() -> Client:
    try:
        return await Client.connect("127.0.0.1:7233", namespace="elis")
    except RuntimeError as exc:
        pytest.skip(f"Temporal dev server not reachable at 127.0.0.1:7233: {exc}")
        raise


@pytest.fixture(autouse=True)
def _reset_sink():
    # notification_activity's default sink is module-level global state --
    # reset it before AND after every test so this file can't leak sink
    # state into other test files' Activity executions.
    set_default_sink(NullNotificationSink())
    yield
    set_default_sink(NullNotificationSink())


@pytest.mark.asyncio
async def test_notification_via_gated_pipeline_never_invokes_hermes_for_routine_events():
    """Real proof, driven through GatedPipelineWorkflow (which is the
    actual T2 caller of deliver_notification_activity) rather than an
    artificial harness: across a full run that hits WAITING_FOR_PO and
    GATE_COMPLETION notifications, run_agent is called exactly twice
    (once for the implementer, once for the validator) -- never for
    either notification."""
    import json

    from elis_temporal.adapter.hermes.adapter import AgentResult, RuntimeIdentity
    from elis_temporal.workflows.gated_pipeline_workflow import GatedPipelineInput, GatedPipelineWorkflow

    client = await _connect_or_skip()
    sink = InMemoryNotificationSink()
    set_default_sink(sink)
    call_log: list[str] = []

    def _identity(profile: str) -> RuntimeIdentity:
        return RuntimeIdentity(os_user="samurai", uid=1000, pid=0, hermes_profile_env=profile, cgroup_path=None, systemd_unit=None)

    def _side_effect(*, profile, **kwargs):
        call_log.append(profile)
        if profile == "elis-pm":
            structured = "real implementation output"
        else:
            structured = json.dumps({"verdict": "PASS"})
        return AgentResult(
            status="completed",
            structured_result=structured,
            evidence_refs=(),
            checkpoint=None,
            usage={"elapsed_seconds": 0.01},
            failure_class=None,
            runtime_identity=_identity(profile),
            capability_result=None,
            correlation_id="notification-proof",
        )

    with patch("elis_temporal.activities.hermes_activity.run_agent", side_effect=_side_effect):
        worker = build_worker_for_profile("elis-pm", client)
        async with worker:
            inp = GatedPipelineInput(
                implementer_profile="elis-pm",
                validator_profile="elis-advisor",
                implementer_instructions="implement",
                validator_instructions="validate",
                execution_id=f"notif-proof-{uuid.uuid4().hex[:8]}",
                po_gate_id="gate-1",
                authorized_po_identities=("carlos",),
            )
            handle = await client.start_workflow(
                GatedPipelineWorkflow.run,
                inp,
                id=f"ELIS/core/gated-pipeline/{uuid.uuid4().hex[:8]}",
                task_queue="elis-pm-queue",
            )
            for _ in range(50):
                stage = await handle.query(GatedPipelineWorkflow.stage)
                if stage == "waiting_for_po":
                    break
                import asyncio

                await asyncio.sleep(0.1)
            assert stage == "waiting_for_po"

            await handle.execute_update(GatedPipelineWorkflow.approve_gate, args=["gate-1", "carlos"])
            result = await handle.result()

    assert result["stage"] == "po_approved"
    # exactly implementer + validator -- notifications never touched run_agent
    assert call_log == ["elis-pm", "elis-advisor"]
    delivered_kinds = [n.kind for n in sink.delivered]
    assert "WAITING_FOR_PO" in delivered_kinds
    assert "GATE_COMPLETION" in delivered_kinds


@pytest.mark.asyncio
async def test_failing_sink_does_not_fail_the_gated_pipeline_workflow():
    """(directive section 14) A notification delivery failure must not
    corrupt/fail the authoritative Workflow -- the pipeline must still
    reach po_approved even though its sink always raises."""
    import json

    from elis_temporal.adapter.hermes.adapter import AgentResult, RuntimeIdentity
    from elis_temporal.workflows.gated_pipeline_workflow import GatedPipelineInput, GatedPipelineWorkflow

    client = await _connect_or_skip()
    set_default_sink(FailingNotificationSink())

    def _identity(profile: str) -> RuntimeIdentity:
        return RuntimeIdentity(os_user="samurai", uid=1000, pid=0, hermes_profile_env=profile, cgroup_path=None, systemd_unit=None)

    def _side_effect(*, profile, **kwargs):
        structured = "real implementation output" if profile == "elis-pm" else json.dumps({"verdict": "PASS"})
        return AgentResult(
            status="completed",
            structured_result=structured,
            evidence_refs=(),
            checkpoint=None,
            usage={"elapsed_seconds": 0.01},
            failure_class=None,
            runtime_identity=_identity(profile),
            capability_result=None,
            correlation_id="notification-failure-proof",
        )

    with patch("elis_temporal.activities.hermes_activity.run_agent", side_effect=_side_effect):
        worker = build_worker_for_profile("elis-pm", client)
        async with worker:
            inp = GatedPipelineInput(
                implementer_profile="elis-pm",
                validator_profile="elis-advisor",
                implementer_instructions="implement",
                validator_instructions="validate",
                execution_id=f"notif-fail-{uuid.uuid4().hex[:8]}",
                po_gate_id="gate-1",
                authorized_po_identities=("carlos",),
            )
            handle = await client.start_workflow(
                GatedPipelineWorkflow.run,
                inp,
                id=f"ELIS/core/gated-pipeline/{uuid.uuid4().hex[:8]}",
                task_queue="elis-pm-queue",
            )
            for _ in range(50):
                stage = await handle.query(GatedPipelineWorkflow.stage)
                if stage == "waiting_for_po":
                    break
                import asyncio

                await asyncio.sleep(0.1)
            assert stage == "waiting_for_po"  # reached despite the sink always raising

            await handle.execute_update(GatedPipelineWorkflow.approve_gate, args=["gate-1", "carlos"])
            result = await handle.result()

    assert result["stage"] == "po_approved"  # workflow completed successfully despite every notification failing
