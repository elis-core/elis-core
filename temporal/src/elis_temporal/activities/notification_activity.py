"""Temporal Activity wrapper for routine notification delivery (T2).

Deliberately never raises -- mirrors adapter.py's own "never raise, report
honestly" convention -- so a notification delivery failure can never fail
or retry-storm the Workflow that triggered it. This Activity does NOT call
the Hermes Adapter / run_agent for any of the routine kinds in
policies/notification.py's NOTIFICATION_KINDS; that is the whole point
(test ledger item 20).
"""

from __future__ import annotations

from temporalio import activity

from elis_temporal.activities.types import DeliverNotificationInput
from elis_temporal.policies.notification import (
    NotificationSink,
    NullNotificationSink,
    build_routine_notification,
)

ACTIVITY_NAME = "deliver_notification_activity"

_default_sink: NotificationSink = NullNotificationSink()


def set_default_sink(sink: NotificationSink) -> None:
    """Test/deployment hook -- production default is NullNotificationSink
    (silent no-op) until a real sink is deliberately wired (T3/T4)."""
    global _default_sink
    _default_sink = sink


def get_default_sink() -> NotificationSink:
    return _default_sink


@activity.defn(name=ACTIVITY_NAME)
def deliver_notification_activity(inp: DeliverNotificationInput) -> dict:
    try:
        notification = build_routine_notification(inp.kind, inp.workflow_id, **inp.fields)
    except ValueError as exc:
        return {"delivered": False, "kind": inp.kind, "error": str(exc)}

    try:
        get_default_sink().deliver(notification)
    except Exception as exc:  # noqa: BLE001 -- delivery must never propagate, see module docstring
        return {"delivered": False, "kind": inp.kind, "error": str(exc)}

    return {"delivered": True, "kind": inp.kind, "error": None}
