from __future__ import annotations

import pytest

from elis_temporal.policies.notification import (
    FailingNotificationSink,
    InMemoryNotificationSink,
    build_routine_notification,
)


def test_build_start_notification():
    n = build_routine_notification("START", "wf-1")
    assert n.kind == "START"
    assert n.workflow_id == "wf-1"
    assert n.requires_ai_generation is False
    assert "wf-1" in n.message


def test_build_waiting_for_po_notification():
    n = build_routine_notification("WAITING_FOR_PO", "wf-1", gate_id="gate-a")
    assert "gate-a" in n.message


def test_unknown_kind_rejected():
    with pytest.raises(ValueError):
        build_routine_notification("NOT_A_REAL_KIND", "wf-1")


def test_in_memory_sink_records_deliveries():
    sink = InMemoryNotificationSink()
    n = build_routine_notification("GATE_COMPLETION", "wf-1", gate_id="g", po_identity="carlos")
    sink.deliver(n)
    assert sink.delivered == [n]


def test_failing_sink_raises():
    sink = FailingNotificationSink()
    n = build_routine_notification("START", "wf-1")
    with pytest.raises(RuntimeError):
        sink.deliver(n)
