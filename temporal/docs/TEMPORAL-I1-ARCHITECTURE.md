# TEMPORAL-I1 Architecture — T0/T1 as actually built

**Status:** pre-authoritative implementation, T0 + T1 scope only. Not validated by Advisor. Not authorized for production. This document describes what exists, not what is proposed.

## What's actually running

- Temporal CLI 1.8.2 (Server 1.31.2, UI 2.50.1), user-space install, no root, no Docker, no Postgres — pinned/checksummed in `deployment/start-dev/VERSION.md`.
- Dev server (`temporal server start-dev`), SQLite-backed at `state/temporal.db`, bound to `127.0.0.1` only for both the gRPC frontend (7233) and Web UI (8233) — confirmed via `ss -tlnp`, not assumed.
- Dedicated `elis` namespace registered alongside the CLI's automatic `default` and internal `temporal-system` namespaces — confirmed via `temporal operator namespace list`.
- Isolated Python 3.11.15 venv at `app/.venv`, `temporalio` 1.31.0, separate from both system Python and the Hermes agent venv.

## The determinism boundary, concretely

Per the discovery finding this plan explicitly incorporates (v2.1 §1.2, §2): Temporal Workflow code must be deterministic and replay-safe. An LLM call is not. Two worked examples, using real incidents already on record this session:

**Example 1 — incident B (blocked-vs-promotion bug, fixed today in Hermes P2 commit `200e999377`).** In Temporal terms, this becomes pure Workflow logic, zero Activities needed for the decision itself:

```python
@workflow.defn
class ElisTaskLifecycle:
    @workflow.run
    async def run(self, task: TaskSpec) -> TaskResult:
        if task.initial_status == "blocked":
            self._sticky_blocked = True   # deterministic state, no LLM involved
        await workflow.wait_condition(lambda: self._dependencies_satisfied)
        if self._sticky_blocked and not self._explicit_unblock_received:
            # parent completion alone can NEVER clear this — the exact bug
            # incident B exposed in the Kanban implementation is structurally
            # unrepresentable here: wait_condition only unblocks on the signal.
            await workflow.wait_condition(lambda: self._explicit_unblock_received)
        ...
```

This is exactly the kind of guarantee Temporal is genuinely good at: incident B could not have happened in this shape, not because an agent remembered a rule, but because the state machine has no code path that clears a sticky block from dependency satisfaction alone.

**Example 2 — PR1-REMOTE-AUTH-01's decomposition step ("should this task split into N subtasks").** This is NOT representable as Workflow logic at all:

```python
@workflow.defn
class ElisTaskLifecycle:
    @workflow.run
    async def run(self, task: TaskSpec) -> TaskResult:
        ...
        # The decomposition JUDGMENT itself is irreducibly non-deterministic —
        # it must be an opaque Activity call. Workflow code cannot decide "should
        # this split" itself; it can only consume the Activity's answer.
        decomposition = await workflow.execute_activity(
            propose_decomposition_activity,   # <-- Hermes/LLM call, wraps run_agent()
            task,
            start_to_close_timeout=timedelta(minutes=10),
        )
        # Everything AFTER this line is deterministic ELIS policy again:
        validated_children = validate_decomposition_policy(decomposition)  # pure function
        for child in validated_children:
            workflow.start_child_workflow(ElisTaskLifecycle.run, child)
```

**Honest conclusion, stated plainly per Carlos's instruction not to round up:** Temporal does not make "an LLM decided to decompose this task" deterministic, and cannot. What it owns instead is everything AROUND that opaque call — recording the Activity's result durably, replaying it identically on worker restart without re-invoking the LLM, and then applying deterministic ELIS policy (`validate_decomposition_policy`) to what came back. That policy layer is real, valuable, and testable — it is where incident A (duplicate creation) and incident B (premature promotion) actually get fixed, structurally, as native Workflow primitives instead of hand-built Kanban-side patches. But the architectural claim should be stated precisely: **Temporal owns durable execution orchestration and policy enforcement around AI decisions, not the AI decisions themselves.** The plan's own §1.2 already states this correctly; this document exists to make it concrete with real code, not just repeat the claim.

## Repository boundary recommendation

Two live org repos exist: `elis-core/elis-core` (platform/governance — "governed multi-agent workflows, auditable evidence") and `elis-core/elis-research` (research content, currently mid-GATE-B rebaseline). **Recommend a new, separate `elis-temporal` repository** rather than embedding in either:

- `elis-core` is the more natural *logical* home (it's the platform/orchestration repo), but it's live, under active branch-protection rulesets, and mid-flight on unrelated governance work (GOVERNANCE.md/MANIFEST.md rebaseline per GATE-B) — landing a large new subsystem there now creates unnecessary coupling and review surface for both efforts.
- `elis-research` is content-domain, not platform — wrong fit regardless of timing.
- A separate repo also directly serves §15's stated goal ("Temporal integration code must not become another patch stack embedded in Hermes") — the same reasoning applies to not embedding it in an existing ELIS repo's history either.

Not created — this is a recommendation for PO/PM to accept, reject, or override, per plan §7's explicit instruction not to create a public repository without approval.

## Six-profile routing — grounded in live state, not assumption

See `app/src/elis_temporal/profiles/routing.py` for the full table with docstrings. Headline finding worth flagging explicitly: **of the six profiles, five have live persistent gateways** (`elis-ideas`, `elis-pm`, `elis-research`, `elis-advisor`, `elis-supervisor` — all confirmed via `systemctl --user list-units`) **and one, `elis-github`, has none** — only `elis-a2a-github.service` (an A2A server) is persistent; GitHub work is dispatcher-invoked per-task. This is presumed deliberate (narrow, credential-isolated, invoke-not-stand-up role) but was not independently confirmed against a governance doc this session — treat as an assumption to verify, not a fact.

## Execution-context-fidelity and capability-preflight — what's real vs. what's deferred

Both are implemented as real, tested Python policy modules (`policies/execution_context.py`, `capabilities/preflight.py`) that make deterministic ALLOW/WAITING_FOR_CAPABILITY/blocked decisions from **observed** facts (the Adapter's `RuntimeIdentity`, environment variables) — not from assumed facts. Explicitly NOT built: any actual credential-routing or principal-enforcement mechanism for `elis-github` — that is Option-A's job (`t_5d9a121f`, still `blocked` as of this session, waiting on Carlos to apply a host-root packet personally). This T0/T1 pass deliberately stops at "compare observed identity to expected identity and report the verdict honestly" rather than inventing how the "expected identity" gets enforced underneath — avoiding exactly the competing-mechanism risk both this plan (§17) and the Hermes P2 session flagged.

## What T2-T4 (not built by this pass) will need from T0/T1

- `run_agent()`'s signature and `AgentResult` shape are stable — build Activities as thin wrappers calling it, don't reimplement subprocess invocation elsewhere.
- `PROFILE_ROUTES` in `profiles/routing.py` is the single source of truth for task-queue names, capability classes, and concurrency policy — Workflow code should read from here, not hardcode profile facts.
- `check_execution_context()` and `check_capability_preflight()` return dataclasses with `.to_dict()` — safe to pass directly into Activity results / Workflow history as JSON-serializable payloads.
- Semantic Workflow-ID policy (plan §10.1) is NOT yet implemented — T2's job.
- Nothing here talks to the live Kanban DB, live gateways, or gh-agentd — by design. T4 (migration/projection) is where that boundary gets crossed, carefully.
