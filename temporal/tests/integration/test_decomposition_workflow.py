"""Proves DecompositionWorkflow against the real dev server -- T2 QA
correction closing the "no live Workflow caller wired to the decomposition
validator yet" residual (directive section 7).

Demonstrates the full required boundary end-to-end through a real Temporal
Workflow: Hermes/LLM Activity proposes -> recorded Activity result ->
deterministic Workflow validation -> only authorized child work proceeds."""

from __future__ import annotations

import json
import uuid
from unittest.mock import patch

import pytest
from temporalio.client import Client

from elis_temporal.adapter.hermes.adapter import AgentResult, RuntimeIdentity
from elis_temporal.workers.worker import build_worker_for_profile
from elis_temporal.workflows.decomposition_workflow import (
    DecompositionWorkflow,
    DecompositionWorkflowInput,
)


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
        correlation_id="decomposition-workflow-test",
    )


def _valid_proposal_json(**overrides) -> str:
    payload = {
        "decision_id": "dec-1",
        "parent_execution_id": "exec-1",
        "parent_profile": "elis-pm",
        "parent_authority_class": "orchestration_decision",
        "proposed_children": [
            {
                "semantic_key": "child-1",
                "role": "elis-ideas",
                "purpose": "draft",
                "required_capabilities": [],
                "authority_class": "cognitive_reasoning",
            }
        ],
        "rationale": "split the work",
    }
    payload.update(overrides)
    return json.dumps(payload)


@pytest.mark.asyncio
async def test_valid_proposal_is_authorized_and_children_returned():
    """A well-formed structured proposal from the Hermes/LLM Activity is
    recorded, then deterministically AUTHORIZED by the Workflow -- proving
    the LLM-proposes/Temporal-authorizes boundary is Workflow-reachable."""
    client = await _connect_or_skip()
    call_log: list[str] = []

    def _side_effect(*, profile, **kwargs):
        call_log.append(profile)
        return _completed(profile, _valid_proposal_json())

    with patch("elis_temporal.activities.hermes_activity.run_agent", side_effect=_side_effect):
        worker = build_worker_for_profile("elis-pm", client)
        async with worker:
            inp = DecompositionWorkflowInput(
                proposer_profile="elis-pm",
                execution_id=f"decomp-authorize-{uuid.uuid4().hex[:8]}",
                proposer_instructions="propose a decomposition",
            )
            handle = await client.start_workflow(
                DecompositionWorkflow.run,
                inp,
                id=f"ELIS/core/decomposition/{uuid.uuid4().hex[:8]}",
                task_queue="elis-pm-queue",
            )
            result = await handle.result()

    assert call_log == ["elis-pm"]
    assert result["stage"] == "authorized"
    assert result["verdict"]["decision"] == "AUTHORIZE"
    assert result["authorized_children"] == [
        {
            "semantic_key": "child-1",
            "role": "elis-ideas",
            "purpose": "draft",
            "required_capabilities": [],
            "dependencies": [],
            "decomposable": True,
            "authority_class": "cognitive_reasoning",
        }
    ]


@pytest.mark.asyncio
async def test_policy_violating_proposal_is_rejected_with_no_authorized_children():
    """A structurally valid but policy-violating proposal (privilege
    escalation: a child claiming higher authority_class than its parent)
    is REJECTED deterministically -- no children are reported authorized,
    proving rejection is genuinely all-or-nothing at the Workflow boundary."""
    client = await _connect_or_skip()

    def _side_effect(*, profile, **kwargs):
        return _completed(
            profile,
            _valid_proposal_json(
                parent_authority_class="cognitive_reasoning",
                proposed_children=[
                    {
                        "semantic_key": "child-1",
                        "role": "elis-github",
                        "purpose": "escalate",
                        "authority_class": "github_mutation",
                    }
                ],
            ),
        )

    with patch("elis_temporal.activities.hermes_activity.run_agent", side_effect=_side_effect):
        worker = build_worker_for_profile("elis-pm", client)
        async with worker:
            inp = DecompositionWorkflowInput(
                proposer_profile="elis-pm",
                execution_id=f"decomp-reject-{uuid.uuid4().hex[:8]}",
                proposer_instructions="propose a decomposition",
            )
            handle = await client.start_workflow(
                DecompositionWorkflow.run,
                inp,
                id=f"ELIS/core/decomposition/{uuid.uuid4().hex[:8]}",
                task_queue="elis-pm-queue",
            )
            result = await handle.result()

    assert result["stage"] == "rejected"
    assert result["verdict"]["decision"] == "REJECT"
    assert result["authorized_children"] == []


@pytest.mark.asyncio
async def test_non_structured_proposal_result_never_reaches_validator():
    """Free prose (not the required structured shape) must land in its own
    distinct "invalid_proposal_result" stage -- never silently coerced into
    either an AUTHORIZE or REJECT verdict."""
    client = await _connect_or_skip()

    def _side_effect(*, profile, **kwargs):
        return _completed(profile, "sure, let's split it into a few pieces")

    with patch("elis_temporal.activities.hermes_activity.run_agent", side_effect=_side_effect):
        worker = build_worker_for_profile("elis-pm", client)
        async with worker:
            inp = DecompositionWorkflowInput(
                proposer_profile="elis-pm",
                execution_id=f"decomp-invalid-{uuid.uuid4().hex[:8]}",
                proposer_instructions="propose a decomposition",
            )
            handle = await client.start_workflow(
                DecompositionWorkflow.run,
                inp,
                id=f"ELIS/core/decomposition/{uuid.uuid4().hex[:8]}",
                task_queue="elis-pm-queue",
            )
            result = await handle.result()

    assert result["stage"] == "invalid_proposal_result"
    assert result["verdict"] is None
    assert result["authorized_children"] == []
