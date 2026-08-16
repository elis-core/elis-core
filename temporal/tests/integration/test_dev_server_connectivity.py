"""Integration test: confirms the real running Temporal dev server
(started under /home/samurai/temporal/state/temporal.db, elis namespace)
is reachable via the Python SDK client, not just the CLI. Skips cleanly if
the dev server isn't running rather than failing the whole suite."""

from __future__ import annotations

import pytest
from temporalio.client import Client


@pytest.mark.asyncio
async def test_can_connect_and_see_elis_namespace():
    try:
        client = await Client.connect("127.0.0.1:7233", namespace="elis")
    except RuntimeError as exc:
        pytest.skip(f"Temporal dev server not reachable at 127.0.0.1:7233: {exc}")
        return

    # A trivial round-trip: list workflows, proving the client/server/
    # namespace triangle is genuinely wired up, not just that a socket
    # accepted a connection. NOTE: this namespace is no longer guaranteed
    # empty as of the T1 routing-wiring correction (test_temporal_routing.py
    # starts real workflow executions here) -- assert the call succeeds and
    # returns a non-negative count, not that it's exactly zero.
    count = 0
    async for _ in client.list_workflows():
        count += 1
    assert count >= 0  # the call itself succeeding is the actual assertion
