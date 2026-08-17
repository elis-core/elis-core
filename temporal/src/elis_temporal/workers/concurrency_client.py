"""Client-side helpers for ProfileExclusivityWorkflow (T2).

Get-or-create + acquire/release, so callers never need to know whether the
per-profile mutex Workflow already exists -- `id_conflict_policy=
USE_EXISTING` makes `start_workflow` a safe no-op against an already-running
singleton instead of erroring, which is the native Temporal mechanism for
this (not a client-side check-then-create race).
"""

from __future__ import annotations

from temporalio.client import Client, WorkflowHandle
from temporalio.common import WorkflowIDConflictPolicy, WorkflowIDReusePolicy

from elis_temporal.policies.concurrency import profile_lock_workflow_id
from elis_temporal.workers.task_queues import TASK_QUEUES
from elis_temporal.workflows.profile_exclusivity_workflow import AcquireRequest, ProfileExclusivityWorkflow


async def get_or_create_profile_lock(client: Client, profile: str) -> WorkflowHandle:
    return await client.start_workflow(
        ProfileExclusivityWorkflow.run,
        id=profile_lock_workflow_id(profile),
        task_queue=TASK_QUEUES[profile],
        id_reuse_policy=WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY,
        id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING,
    )


async def acquire_profile_lock(
    client: Client, profile: str, requester_id: str, *, max_wait_seconds: float = 30
) -> dict:
    handle = await get_or_create_profile_lock(client, profile)
    return await handle.execute_update(
        ProfileExclusivityWorkflow.acquire, AcquireRequest(requester_id=requester_id, max_wait_seconds=max_wait_seconds)
    )


async def release_profile_lock(client: Client, profile: str, requester_id: str) -> None:
    handle = client.get_workflow_handle(profile_lock_workflow_id(profile))
    await handle.signal(ProfileExclusivityWorkflow.release, requester_id)
