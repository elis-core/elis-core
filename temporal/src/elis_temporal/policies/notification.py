"""Lightweight notification primitive (T2, directive section 14).

Routine structural events (START, SUMMARY, WAITING_FOR_PO, validation
result, gate completion) must not require a full Hermes/LLM execution
unless AI-generated content is actually needed -- this module is what lets
Workflow/Activity code emit those without ever touching the Hermes Adapter
for the common case. See activities/notification_activity.py for the
Activity wrapper that makes delivery failures structurally unable to
corrupt Workflow state.

Discord remains reporting/output only, never orchestration truth (directive
section 14) -- nothing anywhere in this codebase reads a delivery outcome
back into a gate/policy decision; deliver_notification_activity's return
value is informational only.

Real Discord/`hermes send` delivery is explicitly NOT wired in T2 (that is
production integration, out of this pilot's scope -- directive section 21
excludes "production GitHub workflow" broadly, and there is no equivalent
Discord-production carve-in). `InMemoryNotificationSink` is what the tests
exercise; a real sink is a T3/T4 concern, structurally ready to slot in
behind the same `NotificationSink` protocol without touching any caller.
"""

from __future__ import annotations

import dataclasses
from typing import Protocol

NOTIFICATION_KINDS = ("START", "SUMMARY", "WAITING_FOR_PO", "VALIDATION_RESULT", "GATE_COMPLETION")

_TEMPLATES: dict[str, str] = {
    "START": "[{workflow_id}] started",
    "SUMMARY": "[{workflow_id}] summary: {summary}",
    "WAITING_FOR_PO": "[{workflow_id}] waiting for PO approval (gate={gate_id})",
    "VALIDATION_RESULT": "[{workflow_id}] validation result: {verdict}",
    "GATE_COMPLETION": "[{workflow_id}] gate {gate_id} completed by {po_identity}",
}


@dataclasses.dataclass(frozen=True)
class Notification:
    kind: str
    workflow_id: str
    message: str
    requires_ai_generation: bool = False

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


class NotificationSink(Protocol):
    def deliver(self, notification: Notification) -> None: ...  # pragma: no cover - protocol


class InMemoryNotificationSink:
    """What tests exercise -- proves delivery happened without touching a
    real external system."""

    def __init__(self) -> None:
        self.delivered: list[Notification] = []

    def deliver(self, notification: Notification) -> None:
        self.delivered.append(notification)


class NullNotificationSink:
    """Default production-safe no-op -- delivery is opt-in via
    activities.notification_activity.set_default_sink(), never silently
    real."""

    def deliver(self, notification: Notification) -> None:
        pass


class FailingNotificationSink:
    """Used only to prove delivery failures don't corrupt Workflow state
    (directive section 14) -- always raises."""

    def deliver(self, notification: Notification) -> None:
        raise RuntimeError("simulated delivery failure")


def build_routine_notification(kind: str, workflow_id: str, **fields: object) -> Notification:
    if kind not in NOTIFICATION_KINDS:
        raise ValueError(f"unknown notification kind {kind!r}, expected one of {NOTIFICATION_KINDS!r}")
    message = _TEMPLATES[kind].format(workflow_id=workflow_id, **fields)
    return Notification(kind=kind, workflow_id=workflow_id, message=message, requires_ai_generation=False)
