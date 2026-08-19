# PO DECISION RECORD — HERMES v0.20.2 MAINTENANCE ACCEPTED

record_id: PO-DR-20260817-HERMES-MAINT-ACCEPTED
date: 2026-08-17
pe: TEMPORAL-I1
gate: Hermes v0.20.2 Maintenance Gate (HMP + HMV + PO-directed factual closeout)
requester: PO Carlos Rocha
verdict: ACCEPTED
next_decision: ELIS-GITHUB-RUNTIME-ALIGNMENT pre-application review (separately gated)
next_decision_await: on PO / independently gated pre-application review sequence
artefact_path: artefacts/TEMPORAL-I1/HERMES-MAINT-GATE/PO-DECISION-RECORD-20260817-HERMES-MAINT-ACCEPTED.md

## Accepted live Hermes state

- Candidate: `5600de8c00eaf3d49f462d1325881ba33754c0da`
- Release provenance:
  - `refs/tags/v2026.8.16` = annotated tag object `bbc20510676c48c6bfa0ef5c2eeefbf676449456`
  - which peels to release commit `df4b65147d7ddd74dd449f9067aabbca5aef0ec7`
  - which is an ancestor of the accepted transitional candidate

## Acceptance basis (PO)

- authorized live application completed
- Hermes v0.20.2 operational
- source clean at exact accepted candidate
- dependencies installed
- shared + 36 profile configs migrated to v37
- intended gateway/dashboard topology healthy
- generic gateway intentionally retired
- ELIS PM temporarily established as sole mechanical dispatcher
- six post-update canaries PASS
- GitHub capability remained correctly fail-closed
- live Temporal Adapter compatibility PASS
- Temporal T2 regression suite 105/105 PASS
- PM HMP PASS
- Advisor HMV PASS
- PO-directed factual closeout corrections complete
- prior report versions preserved
- corrected HMP/HMV SHA-256 sidecars independently verified

## Final corrected assurance conclusion (PO-ratified)

- **A. Hermes maintenance:** `PASS + NO_UNRESOLVED_HERMES_POST_UPDATE_DEFECT`
- **B. Temporal ↔ Hermes Adapter / T0–T2:** `PASS` — live Adapter + 105/105 regression tests
- **C. Temporal GitHub integration:** `KNOWN NON-BLOCKING ALIGNMENT DEFECTS / PRE-T3 REMEDIATION REQUIRED`

The known Temporal/GitHub defects do not reopen or invalidate this Hermes maintenance acceptance.

This acceptance closes the Hermes v0.20.2 maintenance gate.

## NOT AUTHORIZED by this acceptance

- TEMPORAL-I1 T3/T4
- production Temporal authority
- Kanban cutover
- elis-dispatcher implementation
- SQLite runtime mutation
- live application of the staged elis-github runtime candidate
- GitHub repository synchronization
- gh-agentd/broker mutation
- any credential fallback

## NEXT INITIATIVE (separately gated)

ELIS-GITHUB-RUNTIME-ALIGNMENT — staged candidate `413d546be0a0e3e7a448e5a9563005cabd5e4bfe`, status `READY_FOR_PREAPPLICATION_REVIEW`. Proceed only with its independently gated pre-application review sequence. After that, separately:
1. ELIS GitHub runtime alignment / sanctioned GitHub path
2. dedicated elis-dispatcher topology
3. SQLite runtime hardening
4. TEMPORAL-I1 T3

No subsequent initiative is automatically released by this acceptance.

## Exclusions

This acceptance does not authorise T3/T4, production Temporal authority, Kanban cutover, elis-dispatcher implementation, SQLite mutation, elis-github runtime candidate live application, GitHub repo sync, gh-agentd/broker mutation, or any credential fallback.