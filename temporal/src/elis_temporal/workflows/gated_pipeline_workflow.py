"""Implementer -> deterministic preflight -> independent validator ->
durable PO gate (T2, directive section 9-10).

The structural invariants this Workflow encodes (see directive section 9's
required-invariant list, restated here as they map onto code, not just
prose):

  - implementation completion cannot directly release validator
        -> the validator Activity is only ever scheduled after
           policies/preflight.run_deterministic_preflight() passes; a
           "completed" implementer AgentResult that fails structural
           preflight (empty/malformed structured_result) returns
           stage="preflight_failed" and the validator Activity is provably
           never invoked (see test_implementation_cannot_directly_release_validator).

  - deterministic preflight must succeed first
        -> enforced by control flow: the `if not preflight.passed: return`
           happens strictly before the validator `execute_activity` call.

  - implementer cannot satisfy validation
        -> the final "validated" boolean is parsed ONLY from the
           validator's own structured_result (a JSON {"verdict": "PASS"|
           "FAIL"} the validator profile must produce) -- the implementer's
           result is never consulted for this boolean, only used as input
           to the validator's Activity call.

  - Advisor cannot implement work it later validates independently
        -> assert_no_self_validation() raises immediately (before either
           Activity runs) if implementer_profile == validator_profile.

  - validation verdict is separate from Activity completion
        -> a validator Activity that completes (no exception) but returns
           a non-JSON / missing-"verdict" structured_result is its own
           distinct stage ("invalid_validator_result"), never silently
           coerced into either PASS or FAIL.

  - corrections return to implementation inside the same logical Workflow
        -> the `request_correction` signal, handled inside the same
           `run()` loop (same Workflow ID/run), re-invokes the implementer
           Activity rather than starting a new Workflow -- bounded by
           MAX_CORRECTION_CYCLES so a stuck loop cannot run forever.

  - unrelated explicit waits/gates cannot be bypassed by parent/stage
    completion
        -> the PO gate's `approve_gate` Update checks `gate_id` against
           THIS pipeline's own `po_gate_id` and rejects (raises,
           non_retryable) any mismatch -- validator PASS alone never
           satisfies the PO gate, and an approval aimed at a different
           gate_id can never satisfy this one.
"""

from __future__ import annotations

import dataclasses
import json
from datetime import timedelta
from typing import Optional

from temporalio import workflow
from temporalio.exceptions import ApplicationError

from elis_temporal.activities.types import DeliverNotificationInput, RunAgentActivityInput
from elis_temporal.policies.failure_taxonomy import (
    default_hermes_activity_retry_policy,
    is_invalid_structured_result,
)
from elis_temporal.policies.preflight import run_deterministic_preflight

MAX_CORRECTION_CYCLES = 2
CORRECTION_WAIT_TIMEOUT_SECONDS = 3600


def _notification_input(kind: str, workflow_id: str, fields: dict) -> DeliverNotificationInput:
    # Routine notification -- routed through deliver_notification_activity,
    # which never calls the Hermes Adapter (see notification_activity.py's
    # docstring and test_notification.py's proof of this).
    return DeliverNotificationInput(kind=kind, workflow_id=workflow_id, fields=fields)


class SelfValidationError(Exception):
    pass


def assert_no_self_validation(implementer_profile: str, validator_profile: str) -> None:
    if implementer_profile == validator_profile:
        raise SelfValidationError(
            f"implementer_profile == validator_profile == {implementer_profile!r} -- "
            f"self-validation is never permitted, per directive section 9"
        )


@dataclasses.dataclass(frozen=True)
class GatedPipelineInput:
    implementer_profile: str
    validator_profile: str
    implementer_instructions: str
    validator_instructions: str
    execution_id: str
    po_gate_id: str
    authorized_po_identities: tuple[str, ...]
    required_validator_result_keys: tuple[str, ...] = ("verdict",)
    timeout_seconds: int = 600


@workflow.defn(name="GatedPipelineWorkflow")
class GatedPipelineWorkflow:
    def __init__(self) -> None:
        self._po_approved = False
        self._po_approval_record: Optional[dict] = None
        self._correction_requested = False
        self._correction_reason: Optional[str] = None
        self._expected_gate_id: Optional[str] = None
        self._authorized_po_identities: tuple[str, ...] = ()
        self._stage = "starting"

    @workflow.update
    async def approve_gate(self, gate_id: str, po_identity: str) -> dict:
        if gate_id != self._expected_gate_id:
            raise ApplicationError(
                f"gate_id {gate_id!r} does not match this pipeline's gate {self._expected_gate_id!r} -- "
                f"an approval for a different gate can never satisfy this one",
                type="WRONG_GATE",
                non_retryable=True,
            )
        if po_identity not in self._authorized_po_identities:
            raise ApplicationError(
                f"po_identity {po_identity!r} is not among this gate's authorized identities",
                type="UNAUTHORIZED_ACTOR",
                non_retryable=True,
            )
        if self._po_approved:
            return {"approved": True, "gate_id": gate_id, "already_approved": True}
        self._po_approved = True
        self._po_approval_record = {"gate_id": gate_id, "po_identity": po_identity}
        return {"approved": True, "gate_id": gate_id, "already_approved": False}

    @workflow.signal
    def request_correction(self, reason: str) -> None:
        self._correction_requested = True
        self._correction_reason = reason

    @workflow.query
    def stage(self) -> str:
        return self._stage

    @workflow.run
    async def run(self, inp: GatedPipelineInput) -> dict:
        try:
            assert_no_self_validation(inp.implementer_profile, inp.validator_profile)
        except SelfValidationError as exc:
            # Raised as a proper terminal ApplicationError rather than a bare
            # Python exception -- a bare exception from Workflow code is
            # treated by Temporal as a retriable Workflow Task failure (it
            # keeps retrying, assuming a transient/deployment bug), which
            # would silently loop forever instead of failing the Workflow.
            self._stage = "rejected_self_validation"
            raise ApplicationError(str(exc), type="SELF_VALIDATION_REJECTED", non_retryable=True) from exc

        self._expected_gate_id = inp.po_gate_id
        self._authorized_po_identities = inp.authorized_po_identities

        implementer_instructions = inp.implementer_instructions
        implementer_result: dict = {}
        preflight_dict: dict = {}
        validator_result: Optional[dict] = None

        for attempt in range(1, MAX_CORRECTION_CYCLES + 2):
            self._stage = f"implementing_attempt_{attempt}"
            implementer_result = await workflow.execute_activity(
                "run_agent_activity",
                RunAgentActivityInput(
                    profile=inp.implementer_profile,
                    execution_id=f"{inp.execution_id}-impl-{attempt}",
                    instructions=implementer_instructions,
                    timeout_seconds=inp.timeout_seconds,
                ),
                start_to_close_timeout=timedelta(seconds=inp.timeout_seconds + 30),
                retry_policy=default_hermes_activity_retry_policy(),
            )

            self._stage = "preflight"
            preflight = run_deterministic_preflight(implementer_result)
            preflight_dict = preflight.to_dict()
            if not preflight.passed:
                self._stage = "preflight_failed"
                return {
                    "stage": self._stage,
                    "implementer_result": implementer_result,
                    "preflight_result": preflight_dict,
                    "validator_result": None,
                    "po_approval": None,
                }

            self._stage = "validating"
            validator_result = await workflow.execute_activity(
                "run_agent_activity",
                RunAgentActivityInput(
                    profile=inp.validator_profile,
                    execution_id=f"{inp.execution_id}-val-{attempt}",
                    instructions=inp.validator_instructions,
                    input_artifacts={"implementer_result": implementer_result},
                    timeout_seconds=inp.timeout_seconds,
                ),
                start_to_close_timeout=timedelta(seconds=inp.timeout_seconds + 30),
                retry_policy=default_hermes_activity_retry_policy(),
            )

            structured = validator_result.get("structured_result")
            if is_invalid_structured_result(structured, required_keys=inp.required_validator_result_keys):
                self._stage = "invalid_validator_result"
                return {
                    "stage": self._stage,
                    "implementer_result": implementer_result,
                    "preflight_result": preflight_dict,
                    "validator_result": validator_result,
                    "po_approval": None,
                }

            verdict_payload = json.loads(structured)
            validated = verdict_payload.get("verdict") == "PASS"

            if validated:
                break

            if attempt > MAX_CORRECTION_CYCLES:
                self._stage = "rejected"
                return {
                    "stage": self._stage,
                    "implementer_result": implementer_result,
                    "preflight_result": preflight_dict,
                    "validator_result": validator_result,
                    "po_approval": None,
                }

            self._stage = "waiting_for_correction"
            self._correction_requested = False
            await workflow.wait_condition(
                lambda: self._correction_requested,
                timeout=timedelta(seconds=CORRECTION_WAIT_TIMEOUT_SECONDS),
            )
            implementer_instructions = (
                f"{inp.implementer_instructions}\n\nCORRECTION REQUESTED: {self._correction_reason}"
            )
            # loop back to re-implement

        self._stage = "waiting_for_po"
        await workflow.execute_activity(
            "deliver_notification_activity",
            _notification_input("WAITING_FOR_PO", workflow.info().workflow_id, {"gate_id": inp.po_gate_id}),
            start_to_close_timeout=timedelta(seconds=30),
        )
        await workflow.wait_condition(lambda: self._po_approved)

        self._stage = "po_approved"
        await workflow.execute_activity(
            "deliver_notification_activity",
            _notification_input(
                "GATE_COMPLETION",
                workflow.info().workflow_id,
                {"gate_id": self._po_approval_record["gate_id"], "po_identity": self._po_approval_record["po_identity"]},
            ),
            start_to_close_timeout=timedelta(seconds=30),
        )
        return {
            "stage": self._stage,
            "implementer_result": implementer_result,
            "preflight_result": preflight_dict,
            "validator_result": validator_result,
            "po_approval": self._po_approval_record,
        }
