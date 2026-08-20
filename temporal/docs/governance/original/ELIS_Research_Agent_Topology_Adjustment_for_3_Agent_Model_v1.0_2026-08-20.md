# ELIS Research Agent Topology Adjustment for the 3-Agent Model

**Document purpose:** Define how the `elis-research` agent topology should evolve from the prior implementer/validator research-worker pattern to the new ELIS 3-Agent independent research model.

**Date:** 2026-08-20

**Status:** Proposed migration architecture

---

## 1. Executive Summary

The `elis-research` topology should now change in a fundamental way.

The existing research-worker pattern:

```text
stage
  ├── impl
  └── val
```

should no longer be the default architecture for research judgment.

That implementer/validator model remains appropriate for software engineering, where a singular implementation artifact can often be verified through deterministic tests.

For research, especially for Paper 1 and subsequent evidence-intensive workflows, ELIS should use:

```text
stage
  ├── producer-a     Model family A
  ├── producer-b     Model family B
  └── adjudicator-c  Model family C
```

The top-level `elis-research` agent should remain the **Research-domain coordinator**. It should not become Producer A, Producer B, or Adjudicator C.

Temporal should orchestrate the research workers.

Target architecture:

```text
elis-research
    │
    │ Research-domain authority
    │
    ▼
Temporal
    │
    ├── Producer A
    ├── Producer B
    ├── deterministic comparator
    └── Adjudicator C
```

---

# 2. Preserve `elis-slr-*` as the SLR Subdomain Naming Convention

The prior topology decision remains valid:

- `elis-research` is the top-level Research principal;
- `elis-slr` remains valid as the SLR research subdomain;
- `elis-slr-*` remains appropriate for SLR-specific specialist workers.

Therefore the new 3-Agent workers should retain the `elis-slr-*` prefix.

Recommended target naming:

| Stage | Producer A | Producer B | Adjudicator C |
|---|---|---|---|
| Harvest | `elis-slr-harvest-producer-a` | `elis-slr-harvest-producer-b` | `elis-slr-harvest-adjudicator-c` |
| Screen | `elis-slr-screen-producer-a` | `elis-slr-screen-producer-b` | `elis-slr-screen-adjudicator-c` |
| Extract | `elis-slr-extract-producer-a` | `elis-slr-extract-producer-b` | `elis-slr-extract-adjudicator-c` |
| Synthesis | `elis-slr-synth-producer-a` | `elis-slr-synth-producer-b` | `elis-slr-synth-adjudicator-c` |
| Integration | `elis-slr-integration-producer-a` | `elis-slr-integration-producer-b` | `elis-slr-integration-adjudicator-c` |
| Protocol | `elis-slr-protocol-producer-a` | `elis-slr-protocol-producer-b` | `elis-slr-protocol-adjudicator-c` |

This creates a target pool of:

```text
6 research stages
×
3 independent roles
=
18 specialist workers
```

These are intentional methodological triplets, not accidental duplicates.

---

# 3. Current 12-Profile Topology

The current SLR worker pool is:

```text
elis-slr-harvest-impl-a
elis-slr-harvest-val-b

elis-slr-screen-impl-b
elis-slr-screen-val-a

elis-slr-extract-impl-a
elis-slr-extract-val-b

elis-slr-synth-impl-b
elis-slr-synth-val-a

elis-slr-integration-impl-a
elis-slr-integration-val-b

elis-slr-protocol-impl-b
elis-slr-protocol-val-a
```

The existing `a` and `b` suffixes were arbitrary role discriminators.

They were not designed as stable epistemic identities such as:

```text
Producer A = Model family A
Producer B = Model family B
```

For example:

```text
elis-slr-screen-impl-b
elis-slr-screen-val-a
```

does not support a durable invariant in which `a` always represents one model family and `b` another.

Therefore ELIS should not simply reinterpret the current names.

The new research topology should use explicit semantic roles:

```text
producer-a
producer-b
adjudicator-c
```

---

# 4. Do Not Migrate All 18 Profiles Immediately

Although 18 profiles provide a clean target topology, ELIS should not provision or rewrite the entire research worker fleet at once.

Paper 1 should be the migration canary.

The first new triplet should be:

```text
elis-slr-screen-producer-a
elis-slr-screen-producer-b
elis-slr-screen-adjudicator-c
```

and the first Temporal research workflow should be:

```text
Paper1ScreeningWorkflow
```

Migration sequence:

```text
3-Agent architecture
        ↓
one real Paper 1 stage
        ↓
independent validation
        ↓
expand stage by stage
```

This avoids a large 18-profile migration before the methodology has been proven operationally.

---

# 5. Producer A and Producer B Role Design

Producer A and Producer B should have almost symmetrical role definitions.

The scientific task instructions should be materially identical.

Their principal difference should be model identity and independent execution context.

## 5.1 Producer A

Conceptual role:

```text
ROLE:
Independent Research Producer A

MODEL IDENTITY:
Research Model Family A

YOU RECEIVE:
- frozen research task
- frozen protocol
- frozen evidence
- output schema
- acceptance criteria

YOU MUST:
- perform the assigned research judgment independently
- return only the required structured result
- cite evidence locations
- express uncertainty explicitly

YOU MUST NOT:
- inspect Producer B output
- inspect Adjudicator C output
- validate Producer B
- infer another model's answer
- modify protocol
- authorize the final research result
```

## 5.2 Producer B

Conceptual role:

```text
ROLE:
Independent Research Producer B

MODEL IDENTITY:
Research Model Family B
```

Otherwise, Producer B should receive materially the same scientific instructions as Producer A.

That symmetry is important to the methodology.

---

# 6. Adjudicator C Role Design

Adjudicator C should not be a renamed validator.

Its role should be:

```text
ROLE:
Independent Research Adjudicator C
```

Agent C receives:

```text
frozen protocol
original evidence
Producer A result
Producer B result
deterministic comparison
```

Its question is:

```text
What result is actually supported by the evidence and protocol?
```

not:

```text
Which producer sounds better?
```

Recommended verdict vocabulary:

```text
ACCEPT_A
ACCEPT_B
CONVERGENT_RESULT
SYNTHESIZE_SUPPORTED_ELEMENTS
INSUFFICIENT_EVIDENCE
PROTOCOL_AMBIGUITY
HUMAN_ADJUDICATION_REQUIRED
```

Core invariant:

```text
FINAL_RESULT ⊆ SUPPORTED_EVIDENCE
```

C may reconcile supported evidence.

C must not invent an unsupported third result.

---

# 7. Model-Family Independence Must Be a Workflow Invariant

Different model families should not be merely a convention.

Temporal should enforce model-family independence before starting the research activity.

Example configuration:

```yaml
producer_a:
  family_key: family_a
  model_id: ...

producer_b:
  family_key: family_b
  model_id: ...

adjudicator_c:
  family_key: family_c
  model_id: ...
```

Required:

```text
A.family != B.family
A.family != C.family
B.family != C.family
```

Workflow gate:

```text
MODEL_FAMILY_INDEPENDENCE=PASS
```

If violated:

```text
MODEL_FAMILY_INDEPENDENCE=FAIL
WORKFLOW_START=DENIED
```

This rule must also apply to fallback routing.

A provider fallback must not silently select a model belonging to one of the already-used model families.

---

# 8. Record Actual Models, Not Only Configured Models

Every research execution should capture the actual runtime model provenance.

Example:

```yaml
requested_model:
actual_provider:
actual_model:
model_family:
model_version:
prompt_version:
skill_version:
protocol_sha256:
input_sha256:
output_sha256:
```

This is especially important when routing providers or model gateways may dynamically select infrastructure.

The accepted research record should prove which models actually produced A, B, and C.

---

# 9. Research Workers Should Be Stateless

Task-specific scientific conclusions should not accumulate in persistent agent memory.

Otherwise blind independence can be undermined by earlier work.

Target separation:

```text
SOUL
    persistent role identity

SKILLS
    persistent methodology

Temporal input
    task-specific protocol + evidence

Temporal artifact store
    task-specific research output

MEMORY
    no task-specific scientific conclusion transfer
```

Research state should live in:

```text
Temporal
+
immutable evidence artifacts
```

not in conversational memory.

Each research Activity should preferably execute in a fresh isolated session.

---

# 10. Blind Isolation Must Include Tool Access

Blind isolation should be enforced technically.

Producer A should not simply be prompted not to inspect B.

It should receive no path, artifact reference, or lookup capability that exposes B's output.

Temporal should pass:

```text
Producer A:
  input_artifact_id
  protocol_artifact_id

Producer B:
  input_artifact_id
  protocol_artifact_id
```

but not:

```text
Producer A:
  producer_b_output_id
```

Only the comparator and Adjudicator C should receive both outputs.

Core invariant:

```text
A cannot inspect B
B cannot inspect A
```

---

# 11. The Comparator Is Not Agent C

There should be a deterministic comparison component before adjudication.

```text
A output ────┐
             ├── CompareResearchResults()
B output ────┘
```

The comparator can calculate:

```text
exact agreement
field agreement
field disagreement
missing fields
schema mismatch
decision disagreement
confidence difference
```

No LLM should be needed for this operation.

The deterministic policy then decides whether Agent C must run.

---

# 12. Stage-Specific Adjudication Policy

Agent C does not need to run indiscriminately for every activity.

Recommended initial Paper 1 policy:

| Stage | A/B | Agent C |
|---|---|---|
| Harvest | independent where useful | exceptional |
| Screening | mandatory | disagreement only |
| Full-text eligibility | mandatory | disagreement only |
| Extraction | mandatory | conflicting fields |
| Quality assessment | mandatory | disagreement |
| Evidence grading | mandatory | generally always |
| Claim construction | mandatory | always |
| Synthesis | mandatory | always |
| Final scientific conclusions | mandatory | always |

This preserves rigor while controlling model cost.

---

# 13. Existing Six Stages May Need Refinement Later

The current SLR topology contains:

```text
harvest
screen
extract
synth
integration
protocol
```

Paper 1 may expose additional conceptual stages such as:

```text
eligibility
quality-assessment
evidence-grading
claim-construction
```

ELIS should not immediately create additional static profiles for them.

Initially:

- map them through the existing domain skills and Temporal workflows;
- observe actual operational specialization;
- create separate profiles only if evidence shows that persistent specialization is valuable.

Avoid static-agent proliferation before need is demonstrated.

---

# 14. Protocol Workers Require Different Governance

`protocol` should not behave as an ordinary Paper 1 execution stage.

During an active Paper 1 workflow:

```text
protocol = frozen
```

Neither Producer A nor Producer B may change it.

Protocol triplets should instead support controlled:

```text
PROTOCOL_AMENDMENT_PROPOSAL
```

Example:

```text
Protocol Producer A
+
Protocol Producer B
        ↓
Protocol Adjudicator C
        ↓
Human / PO approval
```

An accepted change creates a new protocol version.

It must not silently modify the protocol governing an in-flight workflow.

---

# 15. `elis-research` Must Not Become Adjudicator C

The Research principal should not combine orchestration authority with scientific adjudication.

Avoid:

```text
Producer A
Producer B
      ↓
elis-research decides
```

That would make `elis-research` both:

```text
orchestrator
+
scientific adjudicator
```

The preferred architecture is:

```text
elis-research
      ↓
requests / monitors Temporal workflow
      ↓
Temporal
      ↓
A / B / Comparator / C
      ↓
accepted research result
      ↓
elis-research continues research program
```

Scientific adjudication remains independently evidenced.

---

# 16. Kanban Should Not Dispatch A/B/C

With Temporal now providing the durable orchestration layer, the new research triplets should not be dispatched through Kanban as independent execution-state cards.

Avoid:

```text
elis-research
    ↓
Kanban task A
Kanban task B
Kanban task C
```

Use:

```text
elis-research
       ↓
Temporal Workflow
       ↓
A Activity
B Activity
Comparator
C Activity
```

Kanban may later project state for humans:

```text
Paper 1 Screening
  72% complete
  A/B agreement: 86%
  41 awaiting adjudication
```

but should not be authoritative for execution.

---

# 17. Recommended Migration of the Existing 12 Profiles

## R3-0 — Preserve Current Pool

Do not rename or retire the current 12 immediately.

Classify them as:

```text
legacy research-worker topology
```

and stop assigning new Paper 1 work to them once the new Temporal canary begins.

Do not delete them yet.

---

## R3-1 — Create Only the Paper 1 Screening Triplet

Create:

```text
elis-slr-screen-producer-a
elis-slr-screen-producer-b
elis-slr-screen-adjudicator-c
```

Configure:

```text
A → Model Family A
B → Model Family B
C → Model Family C
```

Then implement:

```text
Paper1ScreeningWorkflow
```

through Temporal.

---

## R3-2 — Prove the Methodology

Required canary acceptance should include:

```text
BLIND_A_B_ISOLATION=PASS
MODEL_FAMILY_INDEPENDENCE=PASS
INPUT_EQUALITY=PASS
OUTPUT_SCHEMA_EQUALITY=PASS
DETERMINISTIC_COMPARATOR=PASS
DISAGREEMENT_ROUTING=PASS
C_EVIDENCE_ACCESS=PASS
C_NO_UNSUPPORTED_SYNTHESIS=PASS
TEMPORAL_REPLAY=PASS
WORKER_RESTART_RECOVERY=PASS
```

Only after this stage is independently validated should ELIS expand the topology.

---

## R3-3 — Expand Stage by Stage

Recommended migration order:

```text
screen
    ↓
extract
    ↓
synth / evidence synthesis
    ↓
integration
    ↓
harvest
    ↓
protocol
```

The exact order may be refined by the Paper 1 implementation plan.

---

## R3-4 — Retire Legacy `impl/val` Profiles

Only after each replacement triplet is proven should the corresponding legacy profiles:

```text
*-impl-*
*-val-*
```

be retired.

Use the same reversible retirement convention already proven elsewhere in ELIS:

```text
archive
↓
dependency verification
↓
move outside active profile-discovery path
↓
post-move verification
↓
retain rollback
```

Do not delete directly.

---

# 18. Target Topology

The eventual Research worker topology becomes:

```text
elis-research
│
├── SLR / Paper workflows
│
├── elis-slr-harvest-producer-a
├── elis-slr-harvest-producer-b
├── elis-slr-harvest-adjudicator-c
│
├── elis-slr-screen-producer-a
├── elis-slr-screen-producer-b
├── elis-slr-screen-adjudicator-c
│
├── elis-slr-extract-producer-a
├── elis-slr-extract-producer-b
├── elis-slr-extract-adjudicator-c
│
├── elis-slr-synth-producer-a
├── elis-slr-synth-producer-b
├── elis-slr-synth-adjudicator-c
│
├── elis-slr-integration-producer-a
├── elis-slr-integration-producer-b
├── elis-slr-integration-adjudicator-c
│
└── elis-slr-protocol-producer-a
    elis-slr-protocol-producer-b
    elis-slr-protocol-adjudicator-c
```

Total target:

```text
1 Research principal
+
18 specialist workers
```

The workers should be understood as:

```text
6 independent research triplets
```

not as eighteen unrelated agents.

---

# 19. Relationship to Software Engineering

ELIS should deliberately support different multi-agent governance patterns by domain.

## Software Engineering

Preferred pattern:

```text
Implementer
    ↓
Independent Validator
```

because the singular implementation artifact can often be verified with deterministic tests and explicit invariants.

## Research

Preferred pattern:

```text
Independent Producer A
+
Independent Producer B
        ↓
Deterministic Comparator
        ↓
Independent Adjudicator C
```

because independent interpretation is itself part of the methodology.

The research architecture therefore should not reuse `impl/val` merely for consistency with code development.

---

# 20. Immediate T3 Research Canary

The recommended first implementation is:

```text
TEMPORAL T3 RESEARCH CANARY
        =
Paper 1 Screening
```

with:

```text
elis-slr-screen-producer-a
+
elis-slr-screen-producer-b
+
elis-slr-screen-adjudicator-c
+
Temporal deterministic comparator
```

This single workflow should prove:

```text
blind independence
model-family independence
structured output equality
deterministic agreement detection
policy-controlled adjudication
evidence-bound C decisions
Temporal durability
replay safety
worker restart recovery
```

before changing the rest of the research fleet.

---

# 21. Proposed Architecture Rule

ELIS should adopt the following rule:

> **For ELIS Research, `impl/val` is deprecated as the default scientific-judgment topology. Each material research judgment should be produced independently by Producer A and Producer B using different model families under blind isolation; their structured outputs should be compared deterministically, and an independent Adjudicator C using a third model family should resolve policy-defined disagreements or high-value scientific conclusions from the original evidence.**

---

# 22. Recommended Migration Principle

The topology change should be:

```text
prove first
expand second
retire third
```

Specifically:

```text
Paper 1 screening triplet
        ↓
Temporal 3-Agent canary PASS
        ↓
independent governance validation
        ↓
additional research-stage triplets
        ↓
legacy impl/val retirement
```

This minimizes migration risk while making Paper 1 the first real production demonstration of the new ELIS 3-Agent research methodology.
