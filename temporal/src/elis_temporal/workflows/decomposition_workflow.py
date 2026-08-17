"""Minimal bounded Workflow integration proving the decomposition boundary
(T2 QA correction, directive section 7).

T2.1 (policies/decomposition.py) built ``validate_decomposition_proposal`` as
a pure, deterministic function and proved it with 28 unit tests -- but no
Workflow anywhere ever called it. Directive section 7 is explicit that a
standalone validator with tests, absent a live Workflow caller, is NOT
sufficient to demonstrate the required architectural boundary:

    Temporal Workflow
    -> Hermes/LLM Activity
    -> structured decomposition proposal
    -> recorded Activity result
    -> deterministic Workflow validation
    -> only authorized child work proceeds

This Workflow closes exactly that gap, and nothing more:

  1. Calls the existing ``run_agent_activity`` (a Hermes/LLM Activity,
     already registered on every profile's Worker -- see workers/worker.py)
     to PROPOSE a decomposition. The proposal is a structured, schema-shaped
     JSON string in ``AgentResult.structured_result`` -- never raw prose that
     mutates topology directly.
  2. That Activity result is durably recorded in Temporal Event History
     (ordinary Activity-result recording, nothing custom).
  3. The proposal is parsed and handed to
     ``policies.decomposition.validate_decomposition_proposal`` --
     deterministically, directly in Workflow code (safe: pure function, no
     IO, per that module's own docstring).
  4. Only children from an AUTHORIZE verdict are reported as ready to
     proceed; a REJECT verdict authorizes nothing.

Deliberately NOT built here (out of this QA correction's bounded scope,
still T3/T4): this Workflow does not start child Workflows for authorized
children. Actually dispatching child work is a representative Core/Research
T3 orchestration concern, not what this correction exists to prove -- it
exists to prove the AUTHORIZATION boundary is real and Workflow-reachable,
which stops at "only authorized child work proceeds" being an accurate,
inspectable Workflow return value.
"""

from __future__ import annotations

import dataclasses
import json
from datetime import timedelta
from typing import Optional

from temporalio import workflow

from elis_temporal.activities.types import RunAgentActivityInput
from elis_temporal.policies.decomposition import (
    ChildProposal,
    DecompositionProposal,
    validate_decomposition_proposal,
)
from elis_temporal.policies.failure_taxonomy import (
    default_hermes_activity_retry_policy,
    is_invalid_structured_result,
)

REQUIRED_PROPOSAL_KEYS = (
    "decision_id",
    "parent_execution_id",
    "parent_profile",
    "parent_authority_class",
    "proposed_children",
    "rationale",
)


@dataclasses.dataclass(frozen=True)
class DecompositionWorkflowInput:
    proposer_profile: str
    execution_id: str
    proposer_instructions: str
    existing_semantic_keys: tuple[str, ...] = ()
    timeout_seconds: int = 600


class MalformedDecompositionProposal(ValueError):
    pass


def _proposal_from_structured(parsed: dict) -> DecompositionProposal:
    try:
        children = tuple(
            ChildProposal(
                semantic_key=child["semantic_key"],
                role=child["role"],
                purpose=child.get("purpose", ""),
                required_capabilities=tuple(child.get("required_capabilities", ())),
                dependencies=tuple(child.get("dependencies", ())),
                decomposable=child.get("decomposable", True),
                authority_class=child.get("authority_class", "cognitive_reasoning"),
            )
            for child in parsed["proposed_children"]
        )
        return DecompositionProposal(
            decision_id=parsed["decision_id"],
            parent_execution_id=parsed["parent_execution_id"],
            parent_profile=parsed["parent_profile"],
            parent_authority_class=parsed["parent_authority_class"],
            proposed_children=children,
            rationale=parsed.get("rationale", ""),
        )
    except (KeyError, TypeError) as exc:
        raise MalformedDecompositionProposal(str(exc)) from exc


@workflow.defn(name="DecompositionWorkflow")
class DecompositionWorkflow:
    @workflow.run
    async def run(self, inp: DecompositionWorkflowInput) -> dict:
        # Phase 1: Hermes/LLM Activity PROPOSES -- never authorizes.
        proposer_result = await workflow.execute_activity(
            "run_agent_activity",
            RunAgentActivityInput(
                profile=inp.proposer_profile,
                execution_id=inp.execution_id,
                instructions=inp.proposer_instructions,
                timeout_seconds=inp.timeout_seconds,
            ),
            start_to_close_timeout=timedelta(seconds=inp.timeout_seconds + 30),
            retry_policy=default_hermes_activity_retry_policy(),
        )

        # Phase 2: recorded Activity result -- ordinary Temporal history,
        # already durable by the time we reach this line.
        structured: Optional[str] = proposer_result.get("structured_result")
        if is_invalid_structured_result(structured, required_keys=REQUIRED_PROPOSAL_KEYS):
            return {
                "stage": "invalid_proposal_result",
                "proposer_result": proposer_result,
                "verdict": None,
                "authorized_children": [],
            }

        try:
            proposal = _proposal_from_structured(json.loads(structured))
        except (MalformedDecompositionProposal, ValueError):
            return {
                "stage": "invalid_proposal_result",
                "proposer_result": proposer_result,
                "verdict": None,
                "authorized_children": [],
            }

        # Phase 3: deterministic Workflow-level AUTHORIZATION.
        verdict = validate_decomposition_proposal(
            proposal, existing_semantic_keys=frozenset(inp.existing_semantic_keys)
        )

        # Phase 4: only an AUTHORIZE verdict yields any authorized child
        # work -- a REJECT is all-or-nothing (see decomposition.py docstring).
        authorized_children = (
            [child.to_dict() for child in proposal.proposed_children]
            if verdict.decision == "AUTHORIZE"
            else []
        )

        return {
            "stage": "authorized" if verdict.decision == "AUTHORIZE" else "rejected",
            "proposer_result": proposer_result,
            "verdict": verdict.to_dict(),
            "authorized_children": authorized_children,
        }
