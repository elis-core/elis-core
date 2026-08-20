# TEMPORAL-I1 T3 Governance Index

This is a derived summary/index only. It does not restate or supersede the
content of the source documents it links to — those documents remain the
sole authoritative source for their own content.

## Source governance documents

| Document | Role | SHA-256 |
|---|---|---|
| [`original/TEMPORAL-I1-PLAN-v2.1-ORIGINAL-20260816.md`](original/TEMPORAL-I1-PLAN-v2.1-ORIGINAL-20260816.md) | `HISTORICAL_ACCEPTED_GOVERNANCE_SOURCE` — the original TEMPORAL-I1 plan (v2.1, 2026-08-16) that T0/T1/T2 were implemented and accepted against | `992a575dc9d6923125704180815498ed1aae2c5b561984e1f4dfc3c935e35bb2` |
| [`original/ELIS_3_Agent_Independent_Research_Model_v1.1_2026-08-20.md`](original/ELIS_3_Agent_Independent_Research_Model_v1.1_2026-08-20.md) | PO-authored architecture — supersedes the original plan's Research-workflow section for material scientific judgment only | `bbd26ee5d417a113b0068d4514bdd58431262d9dc3ba3b163b804b91ed6c5b68` |
| [`original/ELIS_Research_Agent_Topology_Adjustment_for_3_Agent_Model_v1.0_2026-08-20.md`](original/ELIS_Research_Agent_Topology_Adjustment_for_3_Agent_Model_v1.0_2026-08-20.md) | PO-authored topology adjustment accompanying the above | `17a42b80eca06e1bb9d6756983fb19b29eb6bd070ece6a393d3930a7b0dd41d5` |

See also [`TEMPORAL-I1-T3-GITHUB-V3-RECONCILIATION.md`](TEMPORAL-I1-T3-GITHUB-V3-RECONCILIATION.md) for the GitHub-publication workflow's execution-path reconciliation.

## Provenance / supersession chain

```
v2.1 plan (2026-08-16)                         ─┐
                                                  ├─→ T3-G0 (this governance baseline)
3-Agent Research architecture v1.1 / v1.0        │
(2026-08-20)                                    ─┘
                                                   │
                                                   ▼
                                     Amended T3 execution plan
                                (derived from the above, restates nothing)
                                                   │
                                                   ▼
                         T3-C1 → T3-R1 → T3-R2 → T3-G1 → T3-V
```

Later PO architecture decisions **amend** the original T3 plan; they do not
rewrite it. The original plan is preserved byte-for-byte as a historical
source and remains the governing document for anything it defines that the
later decisions do not touch.

## Current status by workflow

- `ORIGINAL_T3_PLAN` = historical accepted source (byte-preserved above)
- `CORE_T3` = `STILL_VALID` — unaffected by the 2026-08-20 amendment; binds to
  the existing, T2-accepted `GatedPipelineWorkflow`
  (`src/elis_temporal/workflows/gated_pipeline_workflow.py`)
- `RESEARCH_T3` = `AMENDED` — the original plan's single Producer→Validator
  pattern for Research is superseded, for material scientific judgment only,
  by the 3-Agent Independent Research Model. The software-engineering
  Implementer→Independent-Validator pattern (used by Core and by ordinary
  engineering work generally) is unaffected and continues unchanged.
- `CURRENT_RESEARCH_ARCHITECTURE` = ELIS 3-Agent Independent Research Model
  v1.1 (Producer A + Producer B, independent model families, blind execution
  → deterministic comparator → Adjudicator C, independent model family, when
  policy requires)
- `ELIS_RESEARCH_PRINCIPAL` = `elis-research` (Research-domain coordinating
  authority; explicitly never becomes Adjudicator C)
- `SLR_SUBDOMAIN_NAMING` = `elis-slr-*` remains valid for SLR-domain workers
  (the existing 12 impl/val profiles are `LEGACY_RESEARCH_WORKER_TOPOLOGY`,
  untouched, retired only after a replacement workflow proves out)
- `GITHUB_T3` — see the separate reconciliation document; conceptual
  workflow shape unchanged, execution path bound to the confirmed-live V3
  mechanism rather than the historical gh-agentd/Option-A assumption

## Current T3 phase sequence

```
T3-G0 → T3-C1 → T3-R1 → T3-R2 → T3-G1 → T3-V
```

- **T3-G0** — governance durability (this baseline). In progress/complete as
  of this commit.
- **T3-C1** — Core representative integration canary. Not started.
- **T3-R1** — Research 3-Agent generic primitives. Not started.
- **T3-R2** — Paper 1 Screening canary (bounded calibration corpus). Not
  started.
- **T3-G1** — GitHub publication representative workflow. Not started.
- **T3-V** — full T3 integration/validation gate. Not started. No single
  phase above completes T3 on its own; T3-V requires all of T3-C1, T3-R1,
  T3-R2, and T3-G1 to be independently accepted first.

Same acceptance chain as T0/T1/T2 applies to each phase: implementation →
Temporal Developer Skill QA → full tests → PM deterministic preflight →
independent Advisor validation → PO acceptance.
