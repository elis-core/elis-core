# TEMPORAL-I1 — PO Decision Record: T2 ACCEPTED; T3 HELD; Hermes Maintenance Gate Ordered

**record_id:** PO-DR-20260817-001
**date:** 2026-08-17
**pe:** TEMPORAL-I1
**gate:** T2
**requester:** PO Carlos Rocha (directive, 2026-08-17)
**evidence_bundle:**
- `artefacts/TEMPORAL-I1/T2P/preflight-report.md` (PM deterministic preflight, PASS)
- `artefacts/TEMPORAL-I1/T2V/advisor-validation-report.md` + `.sha256` (Advisor validation, PASS)
- `temporal/app` commit `7c346445ec83842550bdfb1bee9e2fb24a3521bf`
**verdict:** ACCEPTED (T2)
**authoritative_t2_candidate:** `temporal/app` @ `7c346445ec83842550bdfb1bee9e2fb24a3521bf`

## Confirmed by PO (Advisor independently verified)
- Same exact commit `7c346445…`
- Clean working tree
- temporalio 1.31.0 unchanged
- 105/105 tests PASS, 0 failed/skipped
- No T3/T4 implementation
- No production mutation

## Decisions
1. **T2 is ACCEPTED** based on T2P PASS + T2V `PASS + NO_UNRESOLVED_ELIS_WORKFLOW_POLICY_DEFECT`.
2. **T3 is NOT released.** No T3/T4 creation or dispatch authorized.
3. **Hermes Maintenance / Temporal-Compatibility Gate** ordered before T3, target **Hermes v0.20.2 / tag v2026.8.16** (commit `bbc20510676c48c6bfa0ef5c2eeefbf676449456` per the read-only review).
4. **T2P sidecar closeout:** PM T2P report lacks a detached `.sha256` sidecar — NOT a T2 validation defect, does NOT reopen T2. Narrow closeout ordered via the appropriate runtime/operator actor: compute SHA-256, write detached sidecar, run `sha256sum -c`, record PASS + hash, do NOT modify T2P report contents.
5. **Authority split (binding):** Claude → technical implementation/update packet; PO → authorization; ELIS Supervisor → privileged/runtime application; ELIS PM → deterministic post-update preflight; ELIS Advisor → independent validation where material.

## Exclusions (unchanged, NOT authorised)
No T3/T4 work; no production Temporal authority; no Kanban cutover; no production migration; no GitHub operation; no gateway shutdown; no root mutation. Do NOT float onto upstream `main` without a separate PO decision. Do NOT deploy the 13-commit P2 branch blindly — reconcile against pinned v0.20.2 first. Hermes Kanban remains production-authoritative; Temporal remains pre-authoritative.

## Next decisions
- **next_decision:** Invoke Claude CLI externally for the Hermes maintenance technical implementation packet (bounded scope as prepared by PM).
- **next_decision_await:** PO dispatch of Claude; then PM post-update deterministic preflight → Advisor validation where material → PO acceptance → then T3 release.

**artefact_path:** `artefacts/TEMPORAL-I1/PO-DECISION-RECORD-20260817-T2-ACCEPTED.md` (canonical Core location: `docs/governance/`)
