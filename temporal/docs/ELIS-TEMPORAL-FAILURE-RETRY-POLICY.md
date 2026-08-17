# ELIS Temporal Failure & Retry Policy

T2, directive section 12 (mandatory). Source: `src/elis_temporal/policies/failure_taxonomy.py`, `src/elis_temporal/activities/hermes_activity.py`, `src/elis_temporal/workflows/routing_workflow.py`. Tests: `tests/unit/test_failure_taxonomy.py` (13/13) + `tests/integration/test_failure_retry_semantics.py` (3/3, against the real dev server).

## The gap this closes

T1's `run_agent_activity` always returned `AgentResult.to_dict()` as a normal Activity result, even when `AgentResult.status` was `"failed"`/`"timeout"` — because the Hermes Adapter is deliberately never-raising (see `adapter.py`'s docstring: it observes and reports honestly, it does not decide policy), Temporal's own exception-driven Activity retry never engaged for **any** Hermes-level failure, regardless of `RetryPolicy` configuration. This was disclosed explicitly in the T1 packet as a real, load-bearing gap, not a formality.

## Taxonomy

| Category | Retryable | Notes |
|---|---|---|
| `SUCCESSFUL_SUBSTANTIVE_RESULT` | n/a | Normal Activity result, no error raised — `AgentResult.status == "completed"`. |
| `TRANSIENT_PROVIDER_FAILURE` | Yes | `stderr_tail` matches a known transient marker (connection reset/refused, 502/503, "temporarily unavailable", "network", "interrupted during api call"). |
| `RATE_LIMIT_OR_TRANSIENT_UPSTREAM` | Yes | `stderr_tail` matches "rate limit" or "429" specifically. |
| `TIMEOUT` | Yes (default) | `AgentResult.status == "timeout"`. Treated as transient by default — a caller with evidence a specific timeout is structural, not transient, should bound `RetryPolicy.maximum_attempts` tighter rather than relying on this default. |
| `AUTHORIZATION_DENIED` | No | `capability_result.checked and not capability_result.allowed` — a policy denial, not a Hermes execution failure. Never retryable regardless of stderr content. |
| `INVALID_STRUCTURED_LLM_RESULT` | No | Not produced by `classify_agent_result` directly (that classifies execution outcomes) — this is the classification a **validator's** structured result gets in `GatedPipelineWorkflow` when it isn't parseable JSON with the required keys (`policies/preflight.is_invalid_structured_result` / `policies/failure_taxonomy.is_invalid_structured_result`). Regeneration-on-invalid-result is an explicit policy decision this T2 pass did **not** build (see Deferred, below) — it is surfaced as its own distinct Workflow stage (`"invalid_validator_result"`) instead. |
| `MISSING_HERMES_BINARY_OR_CONFIG_DEFECT` | No | `failure_class == "hermes_binary_not_found"`. A local environment defect — retrying blindly would never succeed and would mask the real problem. Operator-required. |
| `UNCLASSIFIED_HERMES_FAILURE` | No (default) | Any `hermes_exit_N` failure whose `stderr_tail` matches no known transient marker, or any other unrecognized status/failure_class combination. **Deliberately conservative**: an unrecognized failure shape defaults non-retryable rather than risking a blind retry loop against something nobody has characterized yet. |

`WAITING_FOR_CAPABILITY` and `WAITING_FOR_PO` are **not** taxonomy categories — see "Why these can never retry-storm," below.

## Mechanism: one bounded RetryPolicy, not one policy per category

A `RetryPolicy` must be attached to `execute_activity` **before** the Activity runs — but a failure's category is only knowable **after** it fails, from inside the Activity. This is resolved via `ApplicationError.type` matching against `RetryPolicy.non_retryable_error_types`, confirmed directly against the installed `temporalio` 1.31.0 API (see `docs/TEMPORAL-I1-IMPLEMENTATION-REFERENCES.md`): `default_hermes_activity_retry_policy()` returns ONE `RetryPolicy` (`maximum_attempts=4`, `initial_interval=2s`, `backoff_coefficient=2.0`, `maximum_interval=30s` — never Temporal's unbounded default of `maximum_attempts=0`) whose `non_retryable_error_types` names every category in `NON_RETRYABLE_CATEGORIES`. `hermes_activity.run_agent_activity` raises `ApplicationError(message, result_dict, type=classification.category, non_retryable=not classification.retryable)` for any non-success classification. Temporal's own retry logic then does the category-appropriate thing natively: an error whose `type` is in the non-retryable list stops immediately regardless of attempts remaining; any other type retries up to `maximum_attempts`. `RoutingWorkflow` and `GatedPipelineWorkflow` both attach this policy at their `execute_activity` call sites (a small, compatible T1 extension per directive section 20).

## Why `WAITING_FOR_CAPABILITY` / `WAITING_FOR_PO` can never retry-storm

Both are Workflow/policy states, not Activity outcomes, by construction:

- **`WAITING_FOR_CAPABILITY`** is produced by `capabilities/preflight.check_capability_preflight()`, which runs **before** any Workflow is even started (`workers/routing_harness.dispatch_with_capability_gate` short-circuits and returns `{"status": "blocked", "hermes_invoked": False}` without ever calling `client.start_workflow`). There is no Activity execution to retry.
- **`WAITING_FOR_PO`** is a durable `workflow.wait_condition(lambda: self._po_approved)` inside `GatedPipelineWorkflow` — no Activity is scheduled while waiting, so there is nothing for Temporal's Activity-retry mechanism to act on. `test_full_flow_waits_for_po_then_wrong_gate_and_unauthorized_rejected_then_approves` confirms the Workflow genuinely stays `RUNNING` (not completed, not repeatedly re-executing anything) across two rejected approval attempts before the correct one lands.

## What's proven, not just classified

`tests/integration/test_failure_retry_semantics.py`, against the real dev server:

- `test_transient_failure_retries_then_succeeds` — a mocked Hermes call fails twice with a `503`-shaped `stderr_tail`, then succeeds on the third call; the Workflow completes with the eventual success, and the mock's call count is asserted `== 3` (genuinely retried, not just eventually consistent by coincidence).
- `test_missing_binary_never_retries` — exactly one Activity attempt, `ApplicationError.type == "MISSING_HERMES_BINARY_OR_CONFIG_DEFECT"`, `non_retryable is True`.
- `test_authorization_denied_never_retries` — same shape, `type == "AUTHORIZATION_DENIED"`.

## Deferred / not built in T2

- **Regeneration on `INVALID_STRUCTURED_LLM_RESULT`.** The directive allows regeneration "only if policy explicitly permits" — no such policy was specified concretely enough to build; `GatedPipelineWorkflow` surfaces this as a distinct terminal stage (`"invalid_validator_result"`) instead of looping. A future policy could route this into the same `request_correction` signal mechanism already built for validator `FAIL` verdicts, without new Workflow-shape work.
- **Per-category retry-interval tuning beyond the two RATE_LIMIT/TRANSIENT categories sharing one policy.** `RATE_LIMIT_OR_TRANSIENT_UPSTREAM` and `TRANSIENT_PROVIDER_FAILURE` both retry under the same bounded policy today; a real production deployment might want a longer backoff specifically for rate-limit responses (e.g. honoring a `Retry-After` header, which the Adapter does not currently capture). Not built — no such header capture exists yet in `adapter.py`.
