# PO AUTHORIZATION — HERMES v0.20.2 LIVE MAINTENANCE APPLICATION

**Record id:** PO-AUTH-20260817-HERMES-V0.20.2-LIVE
**Date:** 2026-08-17
**Source:** PO Carlos, via ELIS PM channel
**Governing task:** `t_e98c7249` (ELIS Supervisor — Hermes v0.20.2 transitional runtime application)

## Authorized candidate (exact, bound)
- **SHA:** `5600de8c00eaf3d49f462d1325881ba33754c0da`
- **Branch:** `hermes-elis-transitional-v0.20.2`
- **Pinned upstream base:** `bbc20510676c48c6bfa0ef5c2eeefbf676449456` (Hermes v0.20.2 / v2026.8.16)

## Pre-application gates (both PASS — prerequisite met)
- PM deterministic pre-application preflight `t_f8db3b46`: **PASS**
- Advisor independent pre-application validation `t_d406111d`: **PASS + NO_UNRESOLVED_HERMES_TRANSITIONAL_CANDIDATE_OR_TEMPORAL_COMPATIBILITY_DEFECT**

## PO authorized ELIS Supervisor scope
1. Execute validated pre-maintenance snapshot/backup procedure.
2. Apply exact candidate `5600de8c…` (do NOT float to upstream main).
3. Perform validated dependency installation.
4. Perform validated Hermes config migration to target schema.
5. Restart validated gateway/service set per maintenance packet.
6. Execute prescribed zero-production-side-effect profile canaries.
7. Execute prescribed Temporal Adapter compatibility checks.
8. Record exact before/after evidence and runtime state.

## Strict boundaries (NOT authorized)
- Different Hermes commit; upstream main; additional feature development.
- T3/T4. Production Temporal authority. Kanban cutover.
- gh-agentd/Option-A changes. Personal GitHub credential fallback. GitHub production mutations.
- Restoration of legacy top-level elis-slr authority. Unrelated system/runtime changes.
- ELIS Research remains authoritative top-level Research coordinator.

## Rollback / stop conditions
Use the validated rollback plan. Stop and roll back (rather than improvising) if any mandatory condition fails materially — identity mismatch, dependency failure/inconsistent runtime, config migration failure, gateway restart/reconnect failure, incorrect profile identity/routing, multiple Kanban dispatcher ownership, ELIS Research topology regression, Hermes Adapter contract material failure, invalidated T0–T2 assumptions, GitHub not fail-closed, personal credential/PM-context fallback, security/authority boundary weakened, or unexpected source-tree mutation preventing deterministic reconciliation. Do NOT patch around a failed acceptance condition unless the validated packet explicitly authorizes it.

## Mandatory post-update gates (Supervisor completion alone does NOT accept)
```
t_e98c7249  Supervisor live application
  → t_df6b556c  PM deterministic POST-UPDATE preflight (HMP) → PASS
    → t_ce67ccd6  Advisor independent POST-UPDATE validation (HMV) → PASS
      → STOP and return to PO
```
Post-update gates must validate ACTUAL live state: installed version/SHA; source-tree integrity; config migration result; gateway/service health; six-profile canaries; single-dispatcher state; ELIS Research topology; GitHub fail-closed behaviour; Temporal Adapter invocation; accepted T0–T2 compatibility; rollback readiness; absence of unauthorized mutation.

**No T3 release occurs automatically after HMV.** PO separately accepts the completed maintenance gate and authorizes T3.

## Maintenance window
Expected gateway/service downtime ≈10–15 min. Recommended total window 45–60 min. If conditions materially exceed validated assumptions or become ambiguous → STOP and report, do not expand scope.

## Binding authority note
This authorization applies ONLY to the exact candidate and procedure validated by the pre-application gate. Dispatcher promotion is not authorization; this PO-AUTH record is the authorization.
