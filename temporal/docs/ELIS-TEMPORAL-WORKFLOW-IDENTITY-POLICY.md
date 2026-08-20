# ELIS Temporal Workflow Identity Policy

T2, directive section 6. Source: `src/elis_temporal/policies/workflow_identity.py`. Tests: `tests/unit/test_workflow_identity.py` (13/13 passing).

## Scheme

```
ELIS/<domain>/<process>/<semantic-key>
```

- **domain** — e.g. `core`, `research`, `slr`, `platform` (matches ELIS board/domain naming already in use elsewhere on this platform).
- **process** — e.g. `gated-pipeline`, `profile-lock`, `routing`.
- **semantic-key** — caller-supplied, must uniquely identify one logical unit of work within `(domain, process)` — e.g. a Kanban task id, a PR number, a paper/section identifier. This policy does not invent semantic keys; it shapes, validates, and joins them.

Each component must be non-empty and match `^[A-Za-z0-9][A-Za-z0-9._-]*$` (no `/`, no spaces) — enforced by `SemanticWorkflowId.__post_init__`, not left to convention.

## Governing principle

This policy deliberately does not build a second dedup/identity system alongside Temporal's own. Temporal already guarantees Workflow ID uniqueness per Namespace and exposes `WorkflowIDReusePolicy` to control what happens when a start is attempted against an ID with prior history. The ELIS-specific work is (1) choosing a deterministic ID string so equivalent logical work always maps to the same ID, and (2) choosing the right reuse policy per intent — not reimplementing what Temporal's server already enforces.

## Retry vs. correction vs. distinct work

| Case | Mechanism |
|---|---|
| Retry of the same logical work (re-request after transient failure) | SAME semantic key → SAME Workflow ID → start with `WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY`. Temporal itself refuses a new run while the prior run is still running or already succeeded, and only allows a new run once the prior one is failed/canceled/terminated/timed-out. Duplicate logical execution on retry is structurally impossible, not just discouraged. |
| Correction / revalidation of the same logical work | SAME Workflow ID, and **not a new Workflow start at all** — expressed as a Signal/Update against the existing, still-open run (`GatedPipelineWorkflow.request_correction`). There is deliberately no reuse-policy value for "correction," because a correction is not a start. |
| Genuinely distinct work | DIFFERENT semantic key (caller's responsibility — e.g. a different Kanban task id) → different Workflow ID → no collision possible by construction. |
| Concurrent equivalent starts (two callers race to start "the same" work) | Both attempt the SAME Workflow ID under `ALLOW_DUPLICATE_FAILED_ONLY` (or, client-side, `WorkflowIDConflictPolicy.USE_EXISTING` for a get-or-create pattern, as used by `ProfileExclusivityWorkflow`). Temporal's server-side ID uniqueness resolves the race, not a client-side check-then-act. |

`id_reuse_policy_for_intent("initial" | "retry" | "distinct")` returns `ALLOW_DUPLICATE_FAILED_ONLY` for every real case above — no intent maps to plain `ALLOW_DUPLICATE`, because that would let a second concurrent start through against a still-running or already-succeeded ID, which is exactly the duplicate-logical-execution failure mode this policy exists to prevent.

## Applied elsewhere in this codebase

- `ProfileExclusivityWorkflow`'s singleton ID: `ELIS/platform/profile-lock/<profile>` (`policies/concurrency.py`).
- Test IDs throughout `tests/integration/` follow the same scheme (`ELIS/core/gated-pipeline/<uuid>`, `ELIS/core/routing-retry-test/<uuid>`), demonstrating the pattern is usable outside the two built-in call sites.

## Deferred / not built in T2

- **Continue-As-New for long-lived Workflows.** `ProfileExclusivityWorkflow` runs indefinitely and never calls `continue_as_new`, so its Event History grows unbounded over a long deployment lifetime. Not a problem at this pilot's scale — flagged as a T4/production concern, not fixed here (see `docs/TEMPORAL-I1-IMPLEMENTATION-REFERENCES.md`'s "Not consulted this pass" section).
- **Cross-domain/cross-process semantic-key collision detection.** Nothing currently warns if the *same* semantic-key string is reused across two unrelated `(domain, process)` pairs by mistake — the ID would still be structurally distinct (domain/process differ), so this is not a correctness gap, just a missing convenience check. Not built.
