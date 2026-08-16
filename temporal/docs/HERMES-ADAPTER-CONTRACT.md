# Hermes Adapter Contract v1

**Purpose:** the ONLY boundary through which Temporal Workflow/Activity code may interact with the Hermes agent runtime. A future Hermes upgrade should only require re-running this contract's tests against the new Hermes install, never editing Workflow/Activity code — that's the whole point of the boundary (plan §15).

## Interface

```python
def run_agent(
    profile: str,                                    # ELIS profile name, must be one of the six routed profiles
    execution_id: str,                                # caller-supplied identifier for this logical execution
    instructions: str,                                # the prompt/instructions Hermes will run in -z (oneshot) mode
    input_artifacts: Optional[dict[str, Any]] = None, # reserved for future artifact-passing; currently informational only, not yet injected into the prompt
    required_capabilities: Optional[tuple[str, ...]] = None,  # reserved; capability enforcement happens in capabilities/preflight.py BEFORE calling run_agent, not inside it
    execution_context: Optional[dict[str, Any]] = None,       # reserved for future context injection
    correlation_id: Optional[str] = None,             # propagated through unchanged; auto-generated (uuid4) if omitted
    *,
    timeout_seconds: int = 600,
    capability_result: Optional[CapabilityResult] = None,     # attach a preflight verdict for provenance; not enforced here
) -> AgentResult
```

## Contract guarantees

1. **Never raises for expected failure modes.** Timeout, missing binary, and non-zero Hermes exit all return a structured `AgentResult` with `status` set accordingly (`"timeout"`, `"failed"`) — never an unhandled exception. This matters because Activity code calling this must be able to make deterministic-from-Workflow's-perspective decisions from the return value alone.
2. **`runtime_identity` is always observed, never assumed** — even on failure paths. It reflects whatever process actually ran (`os.getuid()`, `/proc/self/cgroup`), not what was requested. This is deliberate: execution-context-fidelity checking needs ground truth, not the caller's intent echoed back.
3. **Process boundary, not import boundary.** This adapter subprocess-invokes the real `hermes -z <prompt>` CLI with `HERMES_PROFILE` set in the environment. It does not import any `hermes_cli.*` module. This is what makes "Hermes upgrade → re-test Adapter" true instead of "Hermes upgrade → reconcile internal API changes."
4. **Blocking/synchronous by design.** Must only be called from inside a Temporal Activity (never Workflow code) — Temporal's own Activity execution model handles the async/worker-thread boundary; this function does not need to.
5. **`structured_result` is raw stdout text today**, not a parsed/typed structure — Hermes's `-z` mode returns "the final content block" per its own docstring, and no JSON-structured oneshot output mode was found to exist in this Hermes version. A future contract version could add a `--json`-style oneshot flag if Hermes gains one; until then, callers needing structured output must parse `structured_result` themselves or instruct the prompt to emit a specific format (e.g. YAML/JSON) and parse it in the calling Activity, not in this adapter.
6. **`evidence_refs` and `checkpoint` are always empty/None in v1** — deliberately not populated. Wiring these to real Kanban evidence/checkpoint paths (mirroring `check_before_claim()` from the Hermes P2 branch) is explicitly T2 scope, not built here, to avoid guessing at a schema decision the Hermes P2 session itself declined to make unilaterally.
7. **`capability_result` is accepted but never computed internally** — this adapter has no opinion on policy. Callers run `capabilities/preflight.py` first and pass the verdict through for provenance only.

## What changes on a Hermes upgrade, and what doesn't

**Should NOT need to change:** `run_agent()`'s signature, `AgentResult`/`RuntimeIdentity`/`CapabilityResult` shapes, the six-profile routing table, the execution-context/capability-preflight policy modules — none of these depend on Hermes internals.

**MAY need to change, and should be caught by re-running `tests/unit/test_hermes_adapter.py` + a live smoke call:**
- The `hermes -z <prompt>` invocation shape itself, if Hermes changes `-z`'s CLI contract.
- `HERMES_PROFILE` as the profile-selection mechanism, if Hermes changes how profile selection works (this is Hermes's own documented mechanism today, confirmed by direct source inspection of `hermes_cli/kanban.py`/`kanban_decompose.py`/`kanban_specify.py`, all of which read `os.environ.get("HERMES_PROFILE")`).
- Exit-code semantics (currently: 0 = success, non-zero = failure, per direct inspection of `hermes_cli/oneshot.py`'s `run_oneshot()`).

## Known gaps in v1 (not silently glossed over)

- No streaming/progress reporting — `run_agent()` blocks until Hermes exits or times out. Long-running agent work (the kind that hits Hermes's own 30-turn iteration budget, documented extensively in this session's memory) will simply show up as an eventual `status="completed"` or `status="timeout"` with no intermediate signal. A future version could add progress heartbeats via `workflow.execute_activity`'s heartbeat mechanism, wrapping this same call — not built here.
- `input_artifacts` is accepted but not actually injected into the prompt yet — the parameter exists in the signature for contract stability, but callers must currently fold any needed context into `instructions` themselves.
