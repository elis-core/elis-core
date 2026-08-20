"""Proves ProfileExclusivityWorkflow against the real dev server -- test
ledger items 13 (different-profile concurrency) and 14 (required
shared-profile exclusivity)."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from temporalio.client import Client, WorkflowUpdateFailedError

from elis_temporal.workers.concurrency_client import acquire_profile_lock, release_profile_lock
from elis_temporal.workers.worker import build_worker_for_profile


async def _connect_or_skip() -> Client:
    try:
        return await Client.connect("127.0.0.1:7233", namespace="elis")
    except RuntimeError as exc:
        pytest.skip(f"Temporal dev server not reachable at 127.0.0.1:7233: {exc}")
        raise


@pytest.mark.asyncio
async def test_same_profile_serializes_two_requesters():
    """(test ledger item 14) A second requester for the SAME profile must
    not acquire until the first releases -- proven by ordering, not just
    both eventually succeeding."""
    client = await _connect_or_skip()
    profile = "elis-pm"  # requires_global_exclusivity(profile) is True
    worker = build_worker_for_profile(profile, client)

    events: list[str] = []

    async def _holder_a():
        result = await acquire_profile_lock(client, profile, "requester-a", max_wait_seconds=10)
        assert result["granted"] is True
        events.append("a-acquired")
        await asyncio.sleep(0.5)
        events.append("a-releasing")
        await release_profile_lock(client, profile, "requester-a")

    async def _holder_b():
        await asyncio.sleep(0.1)  # ensure A acquires first
        result = await acquire_profile_lock(client, profile, "requester-b", max_wait_seconds=10)
        assert result["granted"] is True
        assert result["waited"] is True  # B genuinely had to wait for A
        events.append("b-acquired")
        await release_profile_lock(client, profile, "requester-b")  # clean up -- this is a durable singleton, not test-scoped

    async with worker:
        await asyncio.gather(_holder_a(), _holder_b())

    # B must not acquire before A releases.
    assert events.index("a-releasing") < events.index("b-acquired")


@pytest.mark.asyncio
async def test_different_profiles_do_not_block_each_other():
    """(test ledger item 13) Two DIFFERENT profiles must be able to hold
    their respective locks concurrently -- no cross-profile blocking."""
    client = await _connect_or_skip()
    pm_worker = build_worker_for_profile("elis-pm", client)
    research_worker = build_worker_for_profile("elis-research", client)

    async with pm_worker, research_worker:
        pm_result, research_result = await asyncio.gather(
            acquire_profile_lock(client, "elis-pm", f"pm-{uuid.uuid4().hex[:6]}", max_wait_seconds=5),
            acquire_profile_lock(client, "elis-research", f"research-{uuid.uuid4().hex[:6]}", max_wait_seconds=5),
        )

    assert pm_result["granted"] is True
    assert pm_result["waited"] is False  # no contention -- nothing else held elis-pm's lock
    assert research_result["granted"] is True
    assert research_result["waited"] is False

    # clean up -- these are durable singletons, not test-scoped
    await release_profile_lock(client, "elis-pm", pm_result["requester_id"])
    await release_profile_lock(client, "elis-research", research_result["requester_id"])


@pytest.mark.asyncio
async def test_reacquire_by_current_holder_is_idempotent():
    client = await _connect_or_skip()
    profile = "elis-supervisor"
    worker = build_worker_for_profile(profile, client)
    requester = f"requester-{uuid.uuid4().hex[:6]}"

    async with worker:
        first = await acquire_profile_lock(client, profile, requester, max_wait_seconds=5)
        second = await acquire_profile_lock(client, profile, requester, max_wait_seconds=5)

    assert first["granted"] is True
    assert second["granted"] is True
    assert second["waited"] is False  # same holder re-acquiring is a no-op, not a queue-and-wait

    await release_profile_lock(client, profile, requester)


@pytest.mark.asyncio
async def test_acquire_times_out_safely_rather_than_hanging():
    """"coordination fails safely" (directive section 11) -- a requester
    that can never get the lock within its bound gets a clear failure, not
    an indefinite hang."""
    client = await _connect_or_skip()
    profile = "elis-github"
    worker = build_worker_for_profile(profile, client)
    holder = f"holder-{uuid.uuid4().hex[:6]}"
    blocked = f"blocked-{uuid.uuid4().hex[:6]}"

    async with worker:
        held = await acquire_profile_lock(client, profile, holder, max_wait_seconds=5)
        assert held["granted"] is True
        # second requester must time out, not hang, while holder still holds it
        with pytest.raises(WorkflowUpdateFailedError) as exc_info:
            await acquire_profile_lock(client, profile, blocked, max_wait_seconds=1)
        assert "LOCK_ACQUIRE_TIMEOUT" in str(exc_info.value.cause)

        await release_profile_lock(client, profile, holder)
