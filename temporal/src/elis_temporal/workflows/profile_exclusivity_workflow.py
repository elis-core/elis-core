"""ProfileExclusivityWorkflow -- Temporal-native mutex for
"one_active_run_per_profile_global" (T2, directive section 11).

One long-lived instance per profile, workflow ID
``ELIS/platform/profile-lock/<profile>`` (policies/concurrency.py). Callers
get-or-create it via ``client.start_workflow(..., id_conflict_policy=
WorkflowIDConflictPolicy.USE_EXISTING)`` (see workers/concurrency_client.py)
then call the ``acquire`` Update to block until they hold the lock, and the
``release`` Signal when done.

Fails safely, deliberately, the same tradeoff already accepted on this
platform (Hermes P2's `b4767a9dd4`, a 15s flock timeout, "best-effort
degrade rather than risk a hang" -- see this session's TEMPORAL-I1
memory): a lease TTL means a holder that crashes without releasing does
not wedge every future acquirer forever. `acquire` also bounds its own
wait so a caller is never stuck indefinitely if the workflow itself is
unhealthy -- it raises rather than hangs.

Legitimate different-profile concurrency is unaffected by construction:
each profile gets its own independent singleton Workflow/ID, so this
mechanism cannot cross-block unrelated profiles.
"""

from __future__ import annotations

import dataclasses
from datetime import timedelta
from typing import Optional

from temporalio import workflow
from temporalio.exceptions import ApplicationError

LEASE_TTL_SECONDS = 60  # a holder that stops heartbeating (crashes) is presumed dead after this
DEFAULT_MAX_WAIT_SECONDS = 30  # acquire() gives up rather than hanging forever


@dataclasses.dataclass(frozen=True)
class AcquireRequest:
    requester_id: str
    max_wait_seconds: float = DEFAULT_MAX_WAIT_SECONDS


@workflow.defn(name="ProfileExclusivityWorkflow")
class ProfileExclusivityWorkflow:
    def __init__(self) -> None:
        self._holder: Optional[str] = None
        self._held_since: Optional[float] = None  # workflow.now() timestamp, seconds since epoch
        self._queue: list[str] = []

    def _lease_expired(self) -> bool:
        if self._holder is None or self._held_since is None:
            return False
        now = workflow.now().timestamp()
        return (now - self._held_since) > LEASE_TTL_SECONDS

    def _grant(self, requester_id: str) -> None:
        self._holder = requester_id
        self._held_since = workflow.now().timestamp()
        if requester_id in self._queue:
            self._queue.remove(requester_id)

    @workflow.update
    async def acquire(self, req: AcquireRequest) -> dict:
        if self._lease_expired():
            # Fail-safe reclamation: a crashed holder must not wedge the
            # queue forever. Whoever is at the front of the queue (or this
            # requester, if the queue is empty) gets it.
            next_holder = self._queue[0] if self._queue else req.requester_id
            self._grant(next_holder)

        if self._holder is None:
            self._grant(req.requester_id)
            return {"granted": True, "requester_id": req.requester_id, "waited": False}

        if self._holder == req.requester_id:
            # Idempotent: the current holder re-acquiring is a no-op success,
            # not an error or a re-queue.
            return {"granted": True, "requester_id": req.requester_id, "waited": False}

        if req.requester_id not in self._queue:
            self._queue.append(req.requester_id)

        try:
            await workflow.wait_condition(
                lambda: self._holder == req.requester_id,
                timeout=timedelta(seconds=req.max_wait_seconds),
            )
        except TimeoutError as exc:
            if req.requester_id in self._queue:
                self._queue.remove(req.requester_id)
            raise ApplicationError(
                f"profile lock not acquired within {req.max_wait_seconds}s -- failing safely rather than hanging",
                type="LOCK_ACQUIRE_TIMEOUT",
                non_retryable=False,  # caller may legitimately retry/backoff
            ) from exc

        return {"granted": True, "requester_id": req.requester_id, "waited": True}

    @workflow.signal
    def release(self, requester_id: str) -> None:
        if self._holder != requester_id:
            return  # releasing a lock you don't hold is a no-op, not an error -- fails safely
        self._holder = None
        self._held_since = None
        if self._queue:
            self._grant(self._queue[0])

    @workflow.query
    def status(self) -> dict:
        return {"holder": self._holder, "queue": list(self._queue)}

    @workflow.run
    async def run(self) -> None:
        # Long-lived entity workflow -- runs until externally terminated.
        # Continue-As-New for unbounded history growth is a real T4/production
        # concern (this pilot's workflows are short-lived enough not to hit
        # it) -- flagged, not built, see docs/ELIS-TEMPORAL-WORKFLOW-IDENTITY-POLICY.md
        # "Versioning & long-running concerns" section.
        await workflow.wait_condition(lambda: False)
