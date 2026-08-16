"""Temporal Worker registration for a named ELIS profile's Task Queue.

Minimum real wiring proving the routing architecture: a caller can start a
worker polling exactly one profile's queue, registered with the
RoutingWorkflow and the run_agent_activity Activity. Multiple profiles'
workers are independent Worker instances -- nothing here implies they must
all run in one process or host identity; that remains an open design
question (see the six-profile matrix's expected-vs-actual identity
columns), not something this module resolves.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.worker import Worker

from elis_temporal.activities.hermes_activity import run_agent_activity
from elis_temporal.workers.task_queues import TASK_QUEUES
from elis_temporal.workflows.routing_workflow import RoutingWorkflow


def build_worker_for_profile(profile: str, client: Client, *, max_activity_workers: int = 2) -> Worker:
    if profile not in TASK_QUEUES:
        raise ValueError(f"{profile!r} is not one of the six routed ELIS profiles: {sorted(TASK_QUEUES)}")
    task_queue = TASK_QUEUES[profile]
    return Worker(
        client,
        task_queue=task_queue,
        workflows=[RoutingWorkflow],
        activities=[run_agent_activity],
        activity_executor=ThreadPoolExecutor(max_workers=max_activity_workers),
    )
