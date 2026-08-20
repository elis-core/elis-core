"""Six ELIS profile -> Temporal Task Queue name table.

Single source of truth is profiles/routing.py's PROFILE_ROUTES; this module
just projects the task_queue field for convenient worker/client use.
"""

from __future__ import annotations

from elis_temporal.profiles.routing import PROFILE_ROUTES

TASK_QUEUES: dict[str, str] = {profile: route.task_queue for profile, route in PROFILE_ROUTES.items()}

assert len(TASK_QUEUES) == 6, f"expected exactly 6 routed ELIS profiles, got {len(TASK_QUEUES)}"
assert len(set(TASK_QUEUES.values())) == 6, "task queue names must be pairwise distinct"
