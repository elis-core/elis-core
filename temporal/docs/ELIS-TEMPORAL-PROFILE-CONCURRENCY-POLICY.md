# ELIS Temporal Profile Concurrency Policy

T2, directive section 11. Source: `src/elis_temporal/policies/concurrency.py`, `src/elis_temporal/workflows/profile_exclusivity_workflow.py`, `src/elis_temporal/workers/concurrency_client.py`. Tests: `tests/integration/test_profile_exclusivity.py` (4/4 passing, against the real dev server).

## Policies (unchanged from T1's `profiles/routing.py`)

| `concurrency_policy` value | Profiles | T2 treatment |
|---|---|---|
| `unbounded` | elis-ideas | No exclusivity mechanism — always granted immediately. Not built because it isn't needed. |
| `one_active_run_per_profile_global` | elis-pm, elis-research, elis-supervisor, elis-github | `ProfileExclusivityWorkflow` mutex, this document's subject. |
| `configurable_per_gate` | elis-advisor | **DEFERRED.** No gate-scoped exclusivity variant was specified with enough concreteness to build in T2 — treated as unbounded for now. Flagged in the T2 packet, not silently dropped. |

## Mechanism: Temporal-native mutex, not a custom lock

The directive explicitly warns against assuming Workflow ID uniqueness implements profile exclusivity, and instructs preferring native Worker/Task-Queue/concurrency mechanisms over a custom lock. This implementation is one long-lived singleton Workflow per profile — `ProfileExclusivityWorkflow`, Workflow ID `ELIS/platform/profile-lock/<profile>` (per the [Workflow Identity Policy](ELIS-TEMPORAL-WORKFLOW-IDENTITY-POLICY.md)) — acting as a mutex via a `@workflow.update` handler (`acquire`) that blocks the caller with `workflow.wait_condition` until it becomes the holder, and a `@workflow.signal` (`release`) that hands the lock to the next queued requester. This is Temporal's own documented "entity workflow as a mutex" shape: the concurrency state lives in ordinary Workflow state, durably persisted the same way any other Workflow state is, not in a filesystem lock file or a separate SQL/Kanban lock table (contrast the Hermes P2 remediation's `b4767a9dd4`, a real `flock` at `<kanban_home>/kanban/.profile-claim.lock` — this reimplements the same *invariant*, `ONE_ACTIVE_RUN_PER_PROFILE`, with a genuinely Temporal-native mechanism instead).

Client-side, `workers/concurrency_client.py` provides get-or-create (`client.start_workflow(..., id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING)` — a safe no-op against an already-running singleton, not a client-side check-then-create race) plus `acquire_profile_lock()`/`release_profile_lock()` wrappers.

## Fail-safe behavior

Two independent bounds, both deliberate, both matching this platform's already-accepted tradeoff from the Hermes P2 remediation (`b4767a9dd4`'s 15-second flock timeout, "best-effort degrade rather than risk a hang" — see this session's TEMPORAL-I1 memory):

1. **Lease TTL (60s).** A holder that crashes without calling `release` does not wedge the queue forever — `acquire` checks whether the current holder's lease has expired (`workflow.now() - held_since > LEASE_TTL_SECONDS`) and, if so, force-reclaims the lock for the next queued requester (or the calling requester, if the queue is empty) before proceeding.
2. **Bounded acquire wait (`max_wait_seconds`, default 30s).** A requester that cannot get the lock within its own bound gets a clear, structured failure (`ApplicationError(type="LOCK_ACQUIRE_TIMEOUT", non_retryable=False)`) rather than hanging indefinitely. `non_retryable=False` deliberately — the caller may legitimately retry/backoff, this is not a permanent denial.

Re-acquiring by the current holder is idempotent (a no-op success, not a re-queue) — proven in `test_reacquire_by_current_holder_is_idempotent`. Releasing a lock you don't hold is also a no-op, not an error — same fail-safe philosophy applied symmetrically.

## What's proven, not just asserted

All four integration tests run against the real Temporal dev server (127.0.0.1:7233, `elis` namespace):

- `test_same_profile_serializes_two_requesters` — a second requester for the SAME profile genuinely does not acquire before the first releases, proven by event ordering, not just eventual success.
- `test_different_profiles_do_not_block_each_other` — two DIFFERENT profiles acquire concurrently with zero contention (`waited=False` for both).
- `test_reacquire_by_current_holder_is_idempotent`.
- `test_acquire_times_out_safely_rather_than_hanging` — a requester blocked behind a holder that never releases gets `LOCK_ACQUIRE_TIMEOUT` within its bound, not a hang.

## Deferred / not built in T2

- `configurable_per_gate` for elis-advisor (see table above).
- **Continue-As-New.** `ProfileExclusivityWorkflow.run()` is `await workflow.wait_condition(lambda: False)` — it runs until externally terminated and never bounds its own Event History via `continue_as_new`. Fine for this pilot's scale; a real production concern under sustained load, deferred to T4 (see `docs/TEMPORAL-I1-IMPLEMENTATION-REFERENCES.md`).
- **Fairness beyond FIFO.** The internal `_queue` is a plain list, granting in arrival order — no priority scheme, no starvation protection beyond the lease-TTL reclamation. Not required by anything in the directive, not built speculatively.
