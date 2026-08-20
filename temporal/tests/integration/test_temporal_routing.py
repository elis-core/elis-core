"""Integration tests for the minimal real Temporal SDK wiring (PO bounded
T1 correction #2/#5). All of these run against the real dev server at
127.0.0.1:7233 / namespace elis -- skip cleanly if it isn't reachable.

Test-to-requirement mapping (Carlos's correction #5):
  A -> test_activity_on_ideas_queue_not_consumed_by_pm_only_worker
  B -> test_advisor_queue_dispatch_uses_advisor_hermes_profile
  C -> test_queues_distinguishable_despite_shared_uid  (+ A's behavioral proof)
  D -> test_github_activity_rejected_before_any_hermes_invocation
  E -> covered by tests/unit/test_capability_preflight.py (personal-credential
       fallback never flips availability) -- not duplicated here.
  F -> tests/unit/test_hermes_adapter.py is unmodified by this correction;
       re-run as part of the full suite, not duplicated here.
"""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import patch

import pytest
from temporalio.client import Client

from elis_temporal.activities.types import RunAgentActivityInput
from elis_temporal.adapter.hermes.adapter import AgentResult, RuntimeIdentity
from elis_temporal.workers.routing_harness import dispatch_with_capability_gate
from elis_temporal.workers.worker import build_worker_for_profile


async def _connect_or_skip() -> Client:
    try:
        return await Client.connect("127.0.0.1:7233", namespace="elis")
    except RuntimeError as exc:
        pytest.skip(f"Temporal dev server not reachable at 127.0.0.1:7233: {exc}")
        raise


def _fake_agent_result_for(profile: str) -> AgentResult:
    """A fast, deterministic stand-in for a real Hermes call -- used only in
    tests that are proving Temporal Task-Queue routing/discrimination, not
    Hermes behavior itself (which the one real end-to-end smoke path and the
    unmodified adapter unit tests already cover)."""
    return AgentResult(
        status="completed",
        structured_result=f"fake-result-for-{profile}",
        evidence_refs=(),
        checkpoint=None,
        usage={"elapsed_seconds": 0.01},
        failure_class=None,
        runtime_identity=RuntimeIdentity(
            os_user="samurai",
            uid=1000,
            pid=0,
            hermes_profile_env=profile,
            cgroup_path=None,
            systemd_unit=None,
        ),
        capability_result=None,
        correlation_id="fake",
    )


@pytest.mark.asyncio
async def test_activity_on_ideas_queue_not_consumed_by_pm_only_worker():
    """(A) An Activity addressed to the elis-ideas queue must not be
    consumed by a worker that is only polling the elis-pm queue -- proven
    behaviorally (a workflow started on the ideas queue does not complete
    while only a pm-queue worker is running), not just by comparing queue
    name strings."""
    client = await _connect_or_skip()

    with patch(
        "elis_temporal.activities.hermes_activity.run_agent",
        return_value=_fake_agent_result_for("elis-ideas"),
    ):
        pm_worker = build_worker_for_profile("elis-pm", client)
        async with pm_worker:
            inp = RunAgentActivityInput(
                profile="elis-ideas",
                execution_id=f"routing-discrimination-{uuid.uuid4().hex[:8]}",
                instructions="unused-fake",
                timeout_seconds=5,
            )
            with pytest.raises(asyncio.TimeoutError):
                await dispatch_with_capability_gate(
                    client, "elis-ideas", inp, execution_timeout=2.0
                )
            # nothing polls elis-ideas-queue right now -> must not complete
            # within 2s. Now bring up the correct worker and confirm it DOES
            # complete quickly, proving the mechanism genuinely works when
            # the right worker is present (not just that isolation holds).

        ideas_worker = build_worker_for_profile("elis-ideas", client)
        async with ideas_worker:
            inp2 = RunAgentActivityInput(
                profile="elis-ideas",
                execution_id=f"routing-discrimination-{uuid.uuid4().hex[:8]}",
                instructions="unused-fake",
                timeout_seconds=5,
            )
            result = await dispatch_with_capability_gate(
                client, "elis-ideas", inp2, execution_timeout=10.0
            )
            assert result["hermes_invoked"] is True
            assert result["structured_result"] == "fake-result-for-elis-ideas"


@pytest.mark.asyncio
async def test_advisor_queue_dispatch_uses_advisor_hermes_profile():
    """(B) Dispatch via the elis-advisor queue results in the Adapter being
    invoked with the Advisor logical Hermes profile, not just that the
    queue name matched -- assert on the actual profile argument passed
    into run_agent()."""
    client = await _connect_or_skip()

    captured_profile: dict = {}

    def _capturing_run_agent(*, profile, **kwargs):
        captured_profile["profile"] = profile
        return _fake_agent_result_for(profile)

    with patch(
        "elis_temporal.activities.hermes_activity.run_agent",
        side_effect=_capturing_run_agent,
    ):
        worker = build_worker_for_profile("elis-advisor", client)
        async with worker:
            inp = RunAgentActivityInput(
                profile="elis-advisor",
                execution_id=f"advisor-profile-check-{uuid.uuid4().hex[:8]}",
                instructions="unused-fake",
                timeout_seconds=5,
            )
            result = await dispatch_with_capability_gate(
                client, "elis-advisor", inp, execution_timeout=10.0
            )
            assert result["hermes_invoked"] is True

    assert captured_profile["profile"] == "elis-advisor"


@pytest.mark.asyncio
async def test_queues_distinguishable_despite_shared_uid():
    """(C) Different profile queues remain distinguishable even though every
    profile in this Adapter's current implementation runs under the same
    shared uid 1000 (confirmed live on this host, see docs) -- what
    discriminates dispatch is Task Queue identity, not OS principal. Proven
    by running two profiles' full round trips concurrently in one process
    (same uid throughout) and confirming each gets back its own distinct
    result, not the other's."""
    client = await _connect_or_skip()

    with patch(
        "elis_temporal.activities.hermes_activity.run_agent",
        side_effect=lambda *, profile, **kwargs: _fake_agent_result_for(profile),
    ):
        pm_worker = build_worker_for_profile("elis-pm", client)
        research_worker = build_worker_for_profile("elis-research", client)
        async with pm_worker, research_worker:
            pm_inp = RunAgentActivityInput(
                profile="elis-pm",
                execution_id=f"distinct-{uuid.uuid4().hex[:8]}",
                instructions="unused-fake",
                timeout_seconds=5,
            )
            research_inp = RunAgentActivityInput(
                profile="elis-research",
                execution_id=f"distinct-{uuid.uuid4().hex[:8]}",
                instructions="unused-fake",
                timeout_seconds=5,
            )
            pm_result, research_result = await asyncio.gather(
                dispatch_with_capability_gate(client, "elis-pm", pm_inp, execution_timeout=10.0),
                dispatch_with_capability_gate(
                    client, "elis-research", research_inp, execution_timeout=10.0
                ),
            )

    assert pm_result["structured_result"] == "fake-result-for-elis-pm"
    assert research_result["structured_result"] == "fake-result-for-elis-research"
    assert pm_result["runtime_identity"]["uid"] == research_result["runtime_identity"]["uid"] == 1000


@pytest.mark.asyncio
async def test_github_activity_rejected_before_any_hermes_invocation():
    """(D) A GitHub Activity requiring the unavailable credential is
    rejected (WAITING_FOR_CAPABILITY) strictly before any Hermes/LLM
    invocation -- asserts the Adapter's subprocess boundary is never
    reached, using real (unmocked) host availability state: gh-agentd is
    genuinely unreachable from this uid today."""
    client = await _connect_or_skip()

    inp = RunAgentActivityInput(
        profile="elis-github",
        execution_id=f"github-block-{uuid.uuid4().hex[:8]}",
        instructions="this must never reach hermes",
        timeout_seconds=5,
    )
    with patch("elis_temporal.adapter.hermes.adapter.subprocess.run") as mock_run:
        result = await dispatch_with_capability_gate(client, "elis-github", inp)

    assert result["status"] == "blocked"
    assert result["hermes_invoked"] is False
    assert result["capability_verdict"]["decision"] == "WAITING_FOR_CAPABILITY"
    mock_run.assert_not_called()
