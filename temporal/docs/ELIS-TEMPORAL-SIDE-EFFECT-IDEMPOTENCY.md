# ELIS Temporal External Side-Effect Idempotency

T2, directive section 15. Source: `src/elis_temporal/idempotency/side_effect.py`. Tests: `tests/unit/test_side_effect_idempotency.py` (6/6 passing).

## Contract

```
SideEffectOperation(operation_id, workflow_id, target, desired_state)
    -> apply_idempotent_side_effect(operation, target: SideEffectTarget)
    -> SideEffectOutcome(applied, reconciled, final_state, reasons)
```

`SideEffectTarget` is a two-method Protocol (`read(operation_id)`, `write(operation)`) implemented once per external system (GitHub, Discord, filesystem/artifacts). The orchestration function itself (`apply_idempotent_side_effect`) has zero side-effecting imports — it is pure control flow over whatever `read`/`write` a caller-supplied target provides, which is what makes it safe to unit test deterministically against a fake target rather than a real external system.

Sequence, exactly as specified: **read_before_write → write → read_after_write → reconcile**.

1. **read_before_write.** `target.read(operation.operation_id)` — keyed by `operation_id`, not by any transient request/response artifact. If a prior effect is found and it matches `desired_state`, return immediately with `reconciled=True, applied=False` — no write happens. If a prior effect is found that does **not** match `desired_state`, raise `SideEffectConflictError` rather than silently overwriting a divergent result.
2. **write.** Only reached if step 1 found nothing. `target.write(operation)` performs the real mutation.
3. **read_after_write.** `target.read(operation.operation_id)` again, to verify the mutation actually achieved `desired_state` — never trusting `write()`'s own return value blindly.
4. **reconcile.** If `read_after_write` doesn't confirm `desired_state`, raise `SideEffectConflictError` — the write may have partially failed or been ambiguous, and this is surfaced as a genuine defect rather than papered over.

## Why this closes "ambiguous external mutation reconciles without duplication" (test ledger item 19)

The scenario: a write genuinely succeeds upstream, but the caller's acknowledgment of that success is lost (a real network/process failure mode — e.g. the connection drops between the remote accepting the write and the response reaching the caller). From the caller's perspective this looks identical to an outright failure, so a correct caller retries. Without this framework, a naive retry re-issues the write, potentially creating a duplicate branch/PR/artifact. With it: the retry's `read_before_write` (step 1) discovers the original attempt's real effect under the same `operation_id` and reconciles against it — `test_retry_after_lost_acknowledgment_reconciles_without_duplicate_write` proves this exactly, including asserting the fake target's `write_call_count` stays at `1` after the "retry."

`test_repeated_retries_never_duplicate` extends this to three consecutive calls under the same `operation_id`, still one write. `test_distinct_operation_ids_never_collide` proves the inverse — genuinely different operations never interfere with each other.

## GitHub/Discord: test fixtures only, not production integration

Directive section 15 explicitly forbids mutating production GitHub in T2 ("Do not mutate production GitHub in T2. Use test fixtures/doubles where appropriate."). `FakeGitHubBranchTarget` (in the test file, not shipped as production code) models a "create branch at sha" operation entirely in-memory. A real GitHub-backed `SideEffectTarget` — calling through the sanctioned `elis-github`/`gh-agentd` broker path, per this platform's already-established publication boundary (`docs.temporal.io` was not needed to establish this; see this session's memory of the platform's GitHub publication runbook) — is explicitly **not built**, and is T3/T4 production-integration scope. It is structurally ready to slot in behind the same `SideEffectTarget` Protocol without any change to `apply_idempotent_side_effect` itself.

## Deferred / not built in T2

- Real GitHub/Discord/filesystem `SideEffectTarget` implementations (see above — T3/T4).
- **`retry_behavior` as a first-class configurable field.** The directive's contract lists `retry_behavior` alongside the other fields; this implementation's retry behavior is implicit (caller decides whether/when to retry `apply_idempotent_side_effect` itself, e.g. from within a Temporal Activity with its own `RetryPolicy`) rather than an explicit parameter on `SideEffectOperation`. No concrete requirement specified what a first-class `retry_behavior` field should configure beyond what Activity-level retry policies already provide, so nothing further was invented.
- **Partial/multi-field reconciliation.** `_state_matches` requires every key in `desired_state` to match `observed` exactly (`observed.get(k) == v` for all `k`); there is no concept of "close enough" or partial reconciliation across a subset of fields. Not required by anything in the test ledger.
