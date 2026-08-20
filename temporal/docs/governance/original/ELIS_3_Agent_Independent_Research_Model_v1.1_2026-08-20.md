# ELIS 3-Agent Independent Research Model

**Document purpose:** Define the ELIS 3-Agent research architecture for independent multi-model scientific assessment, deterministic comparison, and evidence-bound adjudication.

**Proposed baseline:** `ELIS_TEMPORAL_INDEPENDENT_RESEARCH_BASELINE_V1`

**Paper 1 baseline:** `ELIS_PAPER1_MULTI_MODEL_RESEARCH_BASELINE_V1`

**Date:** 2026-08-20

**Status:** Revised architecture incorporating independent methodological review; candidate for adoption after Paper 1 calibration pilot

**Revision v1.1:** Incorporates methodological review addressing false agreement, schema-comparison limits, adjudicator bias, calibration, protocol amendments, degraded mode, isolation leakage, human blinding, and enforceable evidence linkage.

---

## 1. Executive Summary

ELIS should adopt a **3-Agent independent research model** for research activities where scientific judgment, interpretation, screening, extraction, evidence grading, or claim construction materially affect the result.

The model replaces the simpler:

```text
Agent A = Research Producer
Agent B = Research Validator
```

with:

```text
Agent A = RESEARCH PRODUCER A
          independent model family A

Agent B = RESEARCH PRODUCER B
          independent model family B

Agent C = RESEARCH ADJUDICATOR
          preferably independent model family C
```

Agents A and B perform the **same research activity independently and blindly**, using the same frozen research contract, source evidence, protocol, ontology/schema, task instructions, and output schema.

Neither A nor B can see the other's result.

Temporal deterministically compares their structured outputs.

Where the result is sufficiently convergent, the workflow may accept the agreement according to the policy defined for that research stage.

Where A and B disagree, or where the research stage requires mandatory adjudication, Agent C receives:

- the original frozen research inputs;
- the original evidence;
- the protocol;
- Producer A's structured result;
- Producer B's structured result;
- a deterministic comparison/diff.

Agent C adjudicates the result against the **original evidence and protocol**.

The model is therefore:

> **Dual Independent Production + Independent Adjudication**

The central methodological objective is to reduce correlated model error, anchoring, confirmation bias, and validator dependence while preserving a deterministic, reproducible, auditable research workflow.

---

# 2. Core Architecture

```text
                  FROZEN RESEARCH INPUT
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
   RESEARCH PRODUCER A     RESEARCH PRODUCER B
      Model family A          Model family B
              │                     │
              │  BLIND ISOLATION    │
              │                     │
              └──────────┬──────────┘
                         ▼
             DETERMINISTIC COMPARATOR
                         │
               ┌─────────┴─────────┐
               │                   │
            AGREEMENT          DISAGREEMENT
               │                   │
               │                   ▼
               │          RESEARCH ADJUDICATOR C
               │             Model family C
               │                   │
               └─────────┬─────────┘
                         ▼
              AUTHORITATIVE RESULT OBJECT
                         │
                         ▼
                 EVIDENCE / PROVENANCE
```

Temporal is the control plane.

The agents are probabilistic reasoning workers.

The workflow state, artifacts, evidence identities, comparisons, authorization, adjudication triggers, and final result status are deterministic.

---

# 3. Research Roles

## 3.1 Agent A — Research Producer A

Agent A independently performs the requested research activity.

Examples:

- screen a paper;
- assess full-text eligibility;
- extract structured evidence;
- assess methodological quality;
- grade evidence;
- propose scientific claims;
- synthesize findings;
- draft evidence-bound research text.

Agent A must not see:

- Agent B's result;
- Agent C's eventual judgment;
- any prompt that reveals another agent's prior conclusion.

## 3.2 Agent B — Research Producer B

Agent B independently performs **the same activity** as Agent A.

It receives the same:

- research question;
- protocol version;
- source material;
- ontology/schema;
- task instructions;
- output schema;
- acceptance criteria.

Its model family should be materially different from Agent A's.

Agent B must not see Agent A's result.

Agent B is not a validator of Agent A.

A and B are epistemic peers.

## 3.3 Agent C — Research Adjudicator

Agent C resolves disagreements or performs mandatory third-party assessment for high-value research outputs.

Agent C receives:

```text
Original frozen research input
Protocol
Original source evidence
Output A
Output B
Deterministic A/B comparison
```

Agent C should not receive hidden reasoning traces from A or B.

Its role is not to determine which model sounds more persuasive.

Its role is to determine which result is best supported by:

```text
evidence
+
protocol
+
structured comparison
```

---

# 4. Blind Independence

Blind isolation must be enforced architecturally, not merely requested in prompts.

Temporal should create two independent activities:

```text
ResearchInputArtifact
        │
        ├── ProducerAActivity
        │      └── OutputA
        │
        └── ProducerBActivity
               └── OutputB
```

Producer A must not receive the artifact reference for Output B.

Producer B must not receive the artifact reference for Output A.

Only after both activities have reached terminal state may the workflow transition to:

```text
A_COMPLETE
+
B_COMPLETE
    ↓
COMPARISON_READY
```

If required:

```text
COMPARISON_READY
    ↓
ADJUDICATION_READY
    ↓
Agent C
```

### Core invariant

```text
A cannot inspect B
B cannot inspect A
```

---

# 5. Input Equality

For independent judgment to be meaningful, A and B should receive the same research contract.

Required equality:

```text
Same research question
Same evidence set
Same protocol
Same inclusion/exclusion rules
Same ontology/schema
Same task instructions
Same output schema
Same acceptance criteria
```

The primary intentional difference should be:

```text
different model family
different model/provider implementation
independent execution context
```

If the evidence or instructions differ, disagreement cannot reliably be interpreted as an independent model judgment.

---

# 6. Model Independence

ELIS should require materially different model families for all three AI roles whenever Agent C is used.

Required AI adjudication pattern:

```text
Producer A
  model family A

Producer B
  model family B

Adjudicator C
  model family C
```

The following are not sufficient forms of independence:

```text
A = same model as B with different temperature
```

or:

```text
A and B = same underlying model through different providers
```

For authoritative AI adjudication, the three family identifiers must be distinct:

```text
A.family != B.family
A.family != C.family
B.family != C.family
```

If a third independent model family is unavailable, ELIS should not silently reuse A's or B's family for C. The workflow should instead transition to:

```text
HUMAN_ADJUDICATION_REQUIRED
```

Provider diversity is desirable in addition to model-family diversity, especially when it reduces shared infrastructure, caching, routing, or implementation dependencies, but provider diversity is secondary to actual model-family independence.

Fallback routing must preserve the same independence invariant. A provider or router must not silently select a fallback model that collides with another active role's model family.

### Governing principle

> Maximize independence of model failure modes while maintaining sufficient capability for the research task. Where the required independent AI family is unavailable, degrade to human adjudication rather than weaken the independence requirement.

The exact models remain configuration, not Workflow logic.

# 7. Reproducibility Metadata

Every agent execution should record the actual runtime configuration and lineage required to reproduce the process and audit model independence.

Minimum metadata:

```yaml
agent_role:
requested_provider:
requested_model:
actual_provider:
actual_model:
model_family:
provider_returned_model_id:
model_version:
temperature:
top_p:
seed_if_supported:
system_prompt_sha256:
task_prompt_sha256:
prompt_version:
skill_version:
output_schema_version:
protocol_version:
protocol_sha256:
input_artifact_sha256:
retrieval_snapshot_id:
retrieval_snapshot_sha256:
presentation_order:
attempt_id:
retry_parent_attempt_id:
degraded_mode:
cache_mode_if_known:
started_at:
completed_at:
output_artifact_sha256:
```

Fields that a provider does not expose, such as a usable random seed, should be recorded explicitly as:

```text
UNAVAILABLE
```

rather than omitted.

The objective is not exact token-by-token LLM reproducibility.

The objective is:

> **process reproducibility, provenance, model-family independence, retry lineage, and auditability.**

The model identifier recorded as authoritative should be the identifier returned by the provider when available, not only the model name requested by the caller.

# 8. Deterministic Comparison Before Adjudication

Agent C should not be used to determine whether A and B agree when agreement can be established mechanically from a frozen structured schema.

Example screening outputs:

```yaml
producer_a:
  decision: INCLUDE
  I1: true
  I2: true
  E1: false

producer_b:
  decision: INCLUDE
  I1: true
  I2: true
  E1: false
```

A deterministic comparator can establish:

```text
OUTCOME_AGREEMENT=TRUE
CRITERION_AGREEMENT=EXACT
AGREEMENT_CLASS=EXACT
```

If:

```text
A = INCLUDE
B = EXCLUDE
```

the deterministic state is:

```text
OUTCOME_AGREEMENT=FALSE
AGREEMENT_CLASS=DISAGREEMENT
ADJUDICATION_REQUIRED=TRUE
```

ELIS should not use a single undifferentiated agreement flag. At minimum, structured stages should distinguish:

```text
EXACT
OUTCOME_ONLY
PARTIAL_FIELDS
DISAGREEMENT
SCHEMA_ERROR
```

For example, if A and B both say `INCLUDE` but cite different inclusion/exclusion criteria, the result is:

```text
OUTCOME_AGREEMENT=TRUE
CRITERION_AGREEMENT=FALSE
AGREEMENT_CLASS=OUTCOME_ONLY
```

That must be logged and must not be silently treated as exact agreement.

The deterministic comparator may compare only fields governed by explicit schema contracts. Free-text semantic equivalence must not be guessed by a string comparator and must not be relabeled "deterministic" by inserting an LLM into the comparison step.

Thus:

```text
probabilistic A/B reasoning
          ↓
schema-governed deterministic comparison
          ↓
policy-controlled adjudication or audit sampling
```

# 9. Adjudicator Decision Vocabulary

Agent C should operate under a constrained decision schema with **orthogonal fields** for the adjudicative verdict and the type of finding.

Recommended `verdict` vocabulary:

```text
ACCEPT_A
ACCEPT_B
CONVERGENT_RESULT
SYNTHESIZE_SUPPORTED_ELEMENTS
NO_AUTHORITATIVE_RESULT
HUMAN_ADJUDICATION_REQUIRED
```

Recommended `finding_category` vocabulary is defined separately in §33 and may contain one or more categories such as:

```text
EVIDENCE_ERROR
EXTRACTION_ERROR
METHODOLOGY_ERROR
INTERPRETATION_DISAGREEMENT
INSUFFICIENT_EVIDENCE
PROTOCOL_AMBIGUITY
```

Example:

```yaml
verdict: HUMAN_ADJUDICATION_REQUIRED
finding_categories:
  - PROTOCOL_AMBIGUITY
```

Agent C must not be forced to manufacture certainty.

`INSUFFICIENT_EVIDENCE` and `PROTOCOL_AMBIGUITY` are finding categories, not competing verdict taxonomies.

# 10. Evidence-Bound Adjudication

Agent C must evaluate both producers against the original frozen evidence and protocol.

Its job is:

```text
evaluate A against evidence
evaluate B against evidence
compare A and B
apply protocol
determine supported result
```

Agent C should not simply choose whichever answer appears better written or more persuasive.

### Core adjudication invariant

```text
FINAL_RESULT ⊆ SUPPORTED_EVIDENCE
```

This must be enforced as a machine-checkable gate, not left as prompt guidance.

Every authoritative element of an adjudicated result must carry at least one `evidence_id` that resolves into the frozen evidence set for the workflow.

A deterministic post-adjudication validator must reject any result that contains:

```text
unknown evidence_id
claim element with zero supporting evidence IDs
evidence ID outside the frozen evidence snapshot
schema-invalid support mapping
```

Required:

```text
EVIDENCE_LINKAGE_VALIDATION=PASS
```

before the result can become authoritative.

Agent C may reconcile.

Agent C may synthesize supported elements.

Agent C must not invent a third unsupported result.

# 11. When Agent C Should Run

ELIS should support two AI-adjudication modes, plus a human audit control for accepted A/B agreements.

## 11.1 Disagreement-Triggered Adjudication

Recommended for high-volume structured decisions.

```text
A + B
  │
  ├─ acceptable structured agreement
  │      ↓
  │ provisional deterministic acceptance
  │      ↓
  │ risk-based random human audit sample
  │
  └─ disagreement / policy divergence
         ↓
         C
```

Suitable for:

- title/abstract screening;
- full-text eligibility;
- ontology-bound extraction fields;
- routine quality criteria.

Agreement is **not** treated as proof of correctness. A risk-based random or stratified sample of the agreed set must be independently human-verified for stages where agreement can directly create an authoritative result. The audit estimates a false-agreement rate and provides an empirical control for correlated A/B error.

The sampling design should be frozen before the production run and should be informed by the calibration pilot, stage risk, prevalence, and target precision rather than by an arbitrary fixed percentage.

## 11.2 Mandatory Adjudication

Recommended for high-value scientific judgments.

```text
A + B
   ↓
C always
```

Suitable for:

- evidence grading;
- major scientific claims;
- synthesis;
- Paper 1 conclusions;
- interpretation of conflicting evidence;
- final claim validation.

Where C is mandatory, agreement sampling serves model-reliability monitoring rather than replacing C.

# 12. Human Escalation

Agent C is not infallible.

The authority chain should therefore be:

```text
Producer A
+
Producer B
      ↓
Adjudicator C where policy requires
      ↓
if unresolved / high-risk
      ↓
Human scientific governance / PO
```

Human escalation must itself minimize anchoring.

For an escalated case, the human reviewer should first receive:

```text
original frozen evidence
protocol
anonymized Result 1
anonymized Result 2
deterministic comparison
```

The reviewer should record a provisional judgment **before** seeing Agent C's verdict.

Only after that provisional judgment is persisted should C's result be revealed for final reconciliation.

The workflow should record:

```text
human_provisional_verdict
c_verdict
human_final_verdict
human_overturned_c
```

This enables measurement of `HUMAN_OVERTURN_C_RATE` and avoids reproducing the same anchoring problem the A/B architecture was designed to prevent.

Human escalation should be available for:

- protocol ambiguity;
- irreducible interpretation disagreement;
- insufficient evidence;
- high-impact claims;
- unexpected model disagreement;
- methodological exceptions.

# 13. Paper 1 as the First Production Research Demonstration

Paper 1 should become the first full production demonstration of the ELIS 3-Agent model.

Its role is larger than producing an academic paper.

Paper 1 should prove that ELIS can conduct research using:

```text
✓ frozen protocol
✓ complete source provenance
✓ blind independent production
✓ different model families
✓ deterministic comparison
✓ explicit disagreement
✓ evidence-bound adjudication
✓ structured extraction
✓ claim-to-evidence traceability
✓ reproducible model configuration
✓ immutable artifacts
✓ Temporal workflow history
✓ human escalation
```

---

# 14. Paper 1 Workflow Architecture

```text
PAPER1_INITIALIZED
       ↓
PROTOCOL_BOUND
       ↓
CALIBRATION_COMPLETE
       ↓
HARVEST_COMPLETE
       ↓
DUAL_TITLE_ABSTRACT_SCREENING_COMPLETE
       ↓
TITLE_ABSTRACT_SCREENING_ADJUDICATED
       ↓
DUAL_FULL_TEXT_ELIGIBILITY_COMPLETE
       ↓
FULL_TEXT_ELIGIBILITY_ADJUDICATED
       ↓
DUAL_EXTRACTION_COMPLETE
       ↓
EXTRACTION_ADJUDICATED
       ↓
DUAL_EVIDENCE_ASSESSMENT_COMPLETE
       ↓
EVIDENCE_ADJUDICATED
       ↓
DUAL_CLAIM_CONSTRUCTION_COMPLETE
       ↓
CLAIMS_ADJUDICATED
       ↓
DUAL_SYNTHESIS_COMPLETE
       ↓
SYNTHESIS_ADJUDICATED
       ↓
DRAFT_COMPLETE
       ↓
FINAL_VALIDATION
       ↓
PO / SCIENTIFIC REVIEW
       ↓
PAPER1_ACCEPTED
```

Temporal owns these states and transitions.

The agents do not.

Title/abstract screening and full-text eligibility are separate stages and must remain separately observable for PRISMA-style reporting and provenance.

# 15. Paper 1 Stage Model

## 15.1 Calibration

Before production screening, ELIS should run a human-reference calibration set that tests:

- protocol wording;
- inclusion/exclusion criteria;
- producer output schema;
- A/B accuracy;
- criterion-level disagreement;
- adjudication behavior.

The reference set should be labeled by qualified human review with disagreement resolution. Its size should be chosen based on the expected prevalence, risk, and precision needs; an initial set in the tens of items may be practical, but the protocol should define the actual design rather than hard-code a universal number.

Calibration must be repeated or requalified when a material model version, prompt, protocol, or schema change occurs.

## 15.2 Harvest

Independent discovery may be useful, but harvesting is primarily a retrieval and deduplication problem.

Possible flow:

```text
Harvester A
+
Harvester B
     ↓
deterministic merge
     ↓
deduplication
     ↓
candidate evidence set
```

Agent C is normally unnecessary unless relevance or source ambiguity requires adjudication.

## 15.3 Screening

Recommended:

```text
Paper
  │
  ├───────────────┐
  ▼               ▼
Screen A        Screen B
Model A         Model B
  │               │
  └──────┬────────┘
         ▼
deterministic comparison
         │
    ┌────┴────┐
    │         │
 AGREED   DISAGREED
    │         │
    ▼         ▼
provisional    C
acceptance
    │
random agreed-set
human audit sample
```

This is methodologically stronger than:

```text
A screens
B reviews A's screening
```

because B cannot be anchored by A.

Screening agreement must distinguish outcome agreement from criterion agreement. Two producers that both return `INCLUDE` for different protocol reasons are not in exact agreement.

# 16. Full-Text Eligibility

A and B independently apply the frozen inclusion/exclusion criteria to the same full text.

This is a distinct workflow state from title/abstract screening and must remain separately reportable.

Output schema should include criterion-level decisions:

```yaml
paper_id:
decision:
inclusion:
  I1:
  I2:
  I3:
exclusion:
  E1:
  E2:
rationale_evidence_ids:
protocol_version:
```

The comparator must report separately:

```text
OUTCOME_AGREEMENT
CRITERION_AGREEMENT
AGREEMENT_CLASS
```

If both producers reach the same eligibility outcome through materially different criteria, the case must be logged as `OUTCOME_ONLY`, not silently accepted as `EXACT`.

Final inclusion/exclusion decisions should be covered by the agreed-set human audit policy unless the stage policy requires C for every item.

# 17. Extraction

Both producers independently populate the same frozen ELIS research schema.

Example:

```yaml
paper_id:
research_question:
method:
country:
election_context:
technology:
threat_or_strategy:
evidence_type:
outcomes:
limitations:
reported_findings:
relevance_to_electoral_integrity:
source_locations:
```

Every authoritative extracted field should carry provenance where practical.

Example:

```yaml
audit_method:
  value: risk-limiting audit
  status: REPORTED
  source:
    page: 14
    section: Methods
    evidence_id: E-P034-014
```

The schema must classify fields by comparison behavior before production:

```text
CLOSED_VOCABULARY
ONTOLOGY_BOUND
NUMERIC
SET_VALUED
EVIDENCE_REFERENCE
FREE_TEXT_NONAUTHORITATIVE
```

Free-text fields may provide explanation but should not determine deterministic agreement unless they are converted into a frozen structured representation first.

Null semantics must not be overloaded. Authoritative fields should use explicit status values such as:

```text
REPORTED
NOT_REPORTED
NOT_APPLICABLE
UNABLE_TO_EXTRACT
UNKNOWN
```

A raw `null` must not ambiguously represent these different conditions.

# 18. Deterministic Extraction Comparison

Because A and B use the same schema, the workflow can compare fields mechanically **only according to the field's declared comparison class**.

Example:

```yaml
A:
  election_technology:
    value: DRE
    status: REPORTED
  audit_method:
    value: RLA
    status: REPORTED

B:
  election_technology:
    value: DRE
    status: REPORTED
  audit_method:
    value: null
    status: NOT_REPORTED
```

The comparator can produce:

```text
FIELD_AGREEMENT:
  election_technology

FIELD_CONFLICT:
  audit_method
```

Comparison rules should include:

- closed vocabulary / ontology-bound fields: exact canonical-ID equality;
- numeric fields: frozen unit normalization and tolerance rules;
- set-valued fields: exact or policy-defined set comparison;
- evidence references: stable evidence-ID comparison;
- free text: excluded from deterministic semantic agreement unless transformed into a frozen structured representation.

The comparator must not treat lexical differences such as:

```text
risk-limiting audit
RLA
```

as a scientific disagreement if both normalize to the same ontology identifier.

Conversely, an LLM-based semantic comparator must not be labeled deterministic.

Agent C should adjudicate only policy-defined unresolved conflicts against the source evidence.

# 19. Quality and Risk Assessment

A and B independently assess methodological quality or bias according to the adopted Paper 1 research protocol.

Agent C adjudicates disagreements in criteria rather than producing an unstructured quality judgment.

The final quality record should preserve:

```text
A judgment
B judgment
agreement/disagreement
C judgment
evidence
final status
```

---

# 20. Evidence Grading

For evidence grading, Agent C should normally be mandatory.

```text
Evidence set
      │
      ├───────────────┐
      ▼               ▼
Grade A           Grade B
      │               │
      └──────┬────────┘
             ▼
             C
             ▼
     ACCEPTED EVIDENCE GRADE
```

The final grade must be evidence-bound and preserve the three-agent provenance.

---

# 21. Claim Construction

Substantive Paper 1 claims should use mandatory A/B/C assessment.

```text
Evidence set
    │
    ├───────────────┐
    ▼               ▼
Claim Producer A  Claim Producer B
    │               │
    └──────┬────────┘
           ▼
   deterministic comparison
           ▼
     Adjudicator C
           ▼
    ACCEPTED CLAIM OBJECT
```

---

# 22. Claim Objects

Every material claim should become a first-class research artifact.

Example:

```yaml
claim_id: P1-C-042

claim:
  text: Independent auditability reduces reliance on software correctness.
  supporting_evidence_ids:
    - E031
    - E044

producer_a:
  verdict: SUPPORTED
  confidence_metadata: HIGH

producer_b:
  verdict: SUPPORTED_WITH_LIMITATION
  confidence_metadata: MEDIUM

agreement:
  class: PARTIAL_FIELDS

adjudicator:
  verdict: SYNTHESIZE_SUPPORTED_ELEMENTS
  finding_categories:
    - INTERPRETATION_DISAGREEMENT
  accepted_evidence_ids:
    - E031
    - E044
  rejected_evidence_ids:
    - E052
  limitations:
    - evidence applies primarily to ...

final_status:
  ACCEPTED
```

Per-stage producer vocabularies must be frozen before production. Self-reported confidence is metadata only and must not drive acceptance, routing, or authority unless a separate calibration study establishes a valid policy use.

No authoritative claim may reach `ACCEPTED` without at least one resolvable evidence ID.

# 23. Claim-to-Evidence Graph

Paper 1 should be generated from accepted evidence objects rather than from free-form LLM memory.

Target chain:

```text
papers
   ↓
validated extraction
   ↓
validated evidence units
   ↓
accepted claim objects
   ↓
validated synthesis
   ↓
Paper 1
```

Not:

```text
papers
   ↓
LLM writes paper
```

A deterministic graph validator must verify before synthesis and publication that:

```text
every accepted claim_id exists
every supporting evidence_id resolves
every evidence_id belongs to the frozen evidence snapshot
no accepted claim has zero support
no draft claim reference points to a rejected claim
```

Required:

```text
CLAIM_EVIDENCE_GRAPH_VALIDATION=PASS
```

This should be a defining ELIS research property.

# 24. Synthesis

For synthesis:

```text
Accepted evidence set
        │
        ├───────────────┐
        ▼               ▼
Synthesis A       Synthesis B
        │               │
        └──────┬────────┘
               ▼
       Adjudicator C
               ▼
      ACCEPTED SYNTHESIS
```

Because synthesis involves high-level interpretation, Agent C should normally run even if A and B substantially agree.

---

# 25. Drafting

Paper drafting should be downstream of accepted claim/evidence objects.

A drafting model must not create scientific claims that are absent from the accepted claim set.

Possible pattern:

```text
Accepted claims + evidence
          ↓
Draft Producer
          ↓
claim-link validator
          ↓
independent scientific review / adjudication
          ↓
accepted section
```

Every substantive paragraph or sentence group should carry machine-readable linkage to one or more accepted `claim_id` values in the source artifact used to generate the publication text.

A deterministic drafting validator must reject:

```text
unknown claim_id
paragraph with substantive scientific assertion but no claim linkage
claim linkage to non-accepted claim
citation/evidence reference outside the accepted graph
```

The human-readable publication may omit internal claim IDs, but the archival/source representation must preserve them.

For high-value sections, independent A/B drafting may also be used.

# 26. Final Paper Validation

Before Paper 1 acceptance, the final paper should be checked against the evidence graph.

Required checks include:

- every substantive claim has evidence;
- citations map to correct papers;
- no unsupported causal inference;
- uncertainty language is preserved;
- limitations are not omitted;
- disagreements are represented appropriately;
- final prose does not exceed the accepted claim set.

---

# 27. Recommended Adjudication Policy by Stage

| Paper 1 Stage | A/B Independent Production | Agent C | Human epistemic control |
|---|---|---|---|
| Calibration | Mandatory pilot | As designed for pilot | Human-reference labels mandatory |
| Harvest | Optional / useful | Only ambiguous relevance | Source/provenance audit |
| Title/abstract screening | Mandatory | On disagreement | Random/stratified audit of agreed set |
| Full-text eligibility | Mandatory | On disagreement | Random/stratified audit of agreed set |
| Extraction | Mandatory | Field conflicts | Audit agreed authoritative fields |
| Quality/risk assessment | Mandatory | On disagreement | Risk-based audit |
| Evidence grading | Mandatory | Usually mandatory | Escalation/high-risk review |
| Claim construction | Mandatory | Mandatory | High-impact claim review available |
| Synthesis | Mandatory | Mandatory | Final scientific review |
| Drafting | Selective | Scientific/editorial adjudication | Claim-link audit + human review |
| Final claim validation | Mandatory | Mandatory or human escalation | Human final governance |

# 28. Deterministic Workflow States

A research stage must not be considered complete merely because an agent reports completion.

Example:

```text
TITLE_ABSTRACT_SCREENING_ADJUDICATED
```

should require machine-verifiable conditions such as:

```text
candidate_count = 612
producer_a_decisions = 612
producer_b_decisions = 612
missing_decisions = 0
exact_agreement_count = ...
outcome_only_agreement_count = ...
disagreement_count = ...
adjudication_records = disagreement_count
agreed_set_audit_sample_planned = true
agreed_set_audit_completed = true
false_agreement_estimate_recorded = true
agreement_statistics_recorded = true
protocol_version_uniform_or_explained = true
artifact_hash_verified = true
schema_validation = PASS
```

Likewise:

```text
EXTRACTION_ADJUDICATED
```

might require:

```text
included_papers = 84
producer_a_records = 84
producer_b_records = 84
comparison_records = 84
unresolved_field_conflicts = 0
agreed_authoritative_field_audit_completed = true
schema_validation = PASS
null_semantics_validation = PASS
provenance_validation = PASS
```

Counts should feed the PRISMA flow records directly where applicable.

This is how ELIS creates deterministic research workflows from probabilistic models.

# 29. Temporal Responsibilities

Temporal should control:

- workflow state;
- activity scheduling;
- A/B isolation;
- artifact references;
- comparison state;
- adjudication triggers;
- retries;
- timeouts;
- human gates;
- final status;
- event history.

Temporal Workflow code must remain deterministic.

---

# 30. Agent Activity Responsibilities

LLM-based operations belong in Temporal Activities.

Examples:

```text
ScreenPaperAActivity
ScreenPaperBActivity
ExtractPaperAActivity
ExtractPaperBActivity
AssessEvidenceAActivity
AssessEvidenceBActivity
ConstructClaimAActivity
ConstructClaimBActivity
AdjudicateClaimActivity
```

LLM/API/filesystem/network operations must not run inside deterministic Workflow code.

---

# 31. Idempotency, Retries, and Degraded Mode

Activities should use stable identifiers.

Example:

```text
workflow_id
paper_id
stage
producer_role
protocol_sha256
input_artifact_sha256
attempt_id
```

A retried Producer A activity must not silently create a second authoritative result.

The workflow should either:

- return the already completed authoritative artifact; or
- create a versioned retry artifact with explicit attempt lineage while retaining provenance.

Retry independence must be defined. A retry should start from the same frozen input snapshot and should not receive the failed attempt's partial scientific conclusion unless the Activity contract explicitly requires recovery data.

A/B independence is about information isolation, not wall-clock simultaneity. A and B should be order-independent and may run concurrently, but sequential execution is acceptable if:

```text
inputs are immutable
retrieval snapshot is identical
no shared mutable research store is visible
no output reference crosses between producers
session state is fresh or equivalently isolated
```

### Degraded mode

If one producer fails terminally after the permitted retry policy:

```text
DUAL_PRODUCTION_COMPLETE=FALSE
DEGRADED_MODE=TRUE
```

A single-producer result must not receive the same authority as a normal 3-Agent result.

Default policy for authoritative Paper 1 decisions:

```text
single producer terminally unavailable
        ↓
no authoritative result
        ↓
retry with approved independent replacement model
or
human adjudication / PO decision
```

Any degraded output retained for diagnostics or exploratory use must carry a durable `degraded_mode: true` provenance flag.

# 32. Agreement, Disagreement, and Reliability as Data

Agreement and disagreement are research-quality measurements, not merely workflow states.

ELIS should record, by stage and criterion where meaningful:

```text
raw agreement rate
positive agreement
negative agreement
exact agreement rate
outcome-only agreement rate
criterion/field disagreement rate
false-agreement rate from human audit
C acceptance rate for A
C acceptance rate for B
C synthesis rate
C order-swap flip rate
human-overturns-C rate
model-specific inclusion tendency
model-specific extraction conflict rate
degraded-mode rate
```

Chance-corrected agreement should be reported from the start of the production pilot rather than deferred.

For binary or categorical screening decisions, ELIS should report at least:

```text
observed/raw agreement
Cohen's kappa for conventional comparability
Gwet's AC1 as a complementary prevalence-robust measure
```

No single coefficient should be treated as ground truth. Kappa and AC1 have different statistical properties; ELIS should report the underlying prevalence/marginals and interpret both cautiously rather than substituting one uncritically for the other.

The calibration pilot should establish provisional alarm thresholds. Production thresholds should be frozen before the main run and should define when to:

```text
continue
increase human audit sampling
pause the stage
recalibrate
replace a model
amend the protocol
```

Model C reliability should also be measured rather than assumed.

# 33. Research Finding Categories

Finding categories are orthogonal to adjudication verdicts.

A result may have one `verdict` and zero or more `finding_categories`.

## EVIDENCE_ERROR

The conclusion is not supported by the source.

## EXTRACTION_ERROR

The source is represented incorrectly.

## METHODOLOGY_ERROR

The protocol or criteria were applied incorrectly.

## INTERPRETATION_DISAGREEMENT

The source is represented accurately, but plausible interpretations differ.

## INSUFFICIENT_EVIDENCE

The source cannot support a reliable conclusion.

## PROTOCOL_AMBIGUITY

The protocol does not deterministically resolve the case.

Example:

```yaml
verdict: HUMAN_ADJUDICATION_REQUIRED
finding_categories:
  - PROTOCOL_AMBIGUITY
  - INSUFFICIENT_EVIDENCE
```

The latter categories may require human escalation rather than automatic correction.

# 34. No Automatic Audit/Fix Loop

ELIS should explicitly prohibit uncontrolled loops such as:

```text
A produces
C criticizes
A automatically rewrites
C criticizes again
repeat
```

Instead:

```text
finding
  ↓
evidence + violated invariant
  ↓
accepted remediation decision
  ↓
one bounded correction
  ↓
new independent assessment
```

---

# 35. Generic Research Primitives

The 3-Agent architecture should not be hard-coded separately for every Paper 1 stage.

Temporal should expose reusable primitives such as:

```text
ProduceIndependentArtifactA
ProduceIndependentArtifactB
CompareArtifacts
AdjudicateArtifacts
RecordDisagreement
EscalateToHuman
AuthorizeResult
```

Domain workflows then compose them:

```text
Paper1ScreeningWorkflow
Paper1ExtractionWorkflow
Paper1EvidenceAssessmentWorkflow
Paper1ClaimWorkflow
Paper1SynthesisWorkflow
```

---

# 36. Relationship to Software Engineering

The ELIS research architecture should deliberately differ from the default software-development model.

For software engineering, the most effective pattern may remain:

```text
Implementer
    ↓
Independent Validator
```

because the implementation artifact is singular and can be verified with deterministic tests.

For research judgment, the preferred architecture is:

```text
Independent Producer A
+
Independent Producer B
        ↓
Independent Adjudicator C
```

because independent interpretation is itself part of the methodology.

Thus ELIS should support multiple governance patterns rather than forcing one pattern across all domains.

---

# 37. ELIS Independent Research Baseline

Proposed baseline:

```text
ELIS_TEMPORAL_INDEPENDENT_RESEARCH_BASELINE_V1

✓ same frozen research contract supplied to A and B
✓ same frozen evidence/retrieval snapshot supplied to A and B
✓ Producer A and Producer B execute blindly
✓ A cannot inspect B
✓ B cannot inspect A
✓ A and B use different model families
✓ authoritative AI Adjudicator C uses a third different model family
✓ if third-family C is unavailable, workflow escalates to human adjudication
✓ outputs use frozen per-stage structured schemas
✓ field comparison classes and null semantics are explicit
✓ deterministic comparison occurs before adjudication
✓ outcome agreement is distinguished from criterion/field agreement
✓ disagreements are explicitly represented
✓ agreed-set human audit estimates false-agreement rate
✓ calibration against human-reference items occurs before production
✓ chance-corrected agreement statistics are reported
✓ C presentation order is anonymized/randomized
✓ C order-swap flip rate is measured on an audit sample
✓ C receives original evidence, not only A/B conclusions
✓ every authoritative result carries resolvable evidence IDs
✓ C cannot silently invent unsupported results
✓ unresolved disagreement can escalate to blinded human review
✓ protocol amendments are versioned with impact analysis
✓ degraded single-producer mode cannot silently become authoritative
✓ agent/model/prompt/schema/protocol versions and retry lineage are recorded
✓ Temporal controls state and authority
✓ complete workflow/event history is retained
```

# 38. Paper 1 Baseline

Proposed first research production milestone:

```text
ELIS_PAPER1_MULTI_MODEL_RESEARCH_BASELINE_V1

Producer A
  independent model family A

Producer B
  independent model family B

Adjudicator C
  independent model family C
  mandatory third-family independence for AI adjudication

blind A/B execution
  mandatory

human-reference calibration
  mandatory before production

structured evidence
  mandatory

frozen producer vocabularies/schema contracts
  mandatory

deterministic comparison
  mandatory for schema-governed fields

explicit disagreement
  mandatory

agreed-set human audit
  mandatory where agreement directly creates authority

chance-corrected agreement reporting
  mandatory

claim-to-evidence provenance
  mandatory

protocol version and amendment log
  mandatory

human escalation
  blinded and available

degraded-mode provenance
  mandatory

Temporal workflow history
  mandatory
```

# 39. Paper 1 Acceptance Objective

Paper 1 should demonstrate:

```text
✓ protocol frozen before production
✓ calibration against a human-reference set
✓ complete source provenance
✓ immutable retrieval/evidence snapshots
✓ independent A/B title/abstract screening
✓ independent A/B full-text eligibility
✓ independent A/B extraction
✓ deterministic disagreement detection for structured fields
✓ outcome agreement distinguished from criterion agreement
✓ agreed-result human audit and false-agreement estimate
✓ chance-corrected agreement statistics
✓ evidence-bound, order-randomized Agent C adjudication
✓ C flip-rate monitoring
✓ structured research objects
✓ claim-to-evidence traceability
✓ deterministic evidence-link validation
✓ model-family independence
✓ reproducible model/prompt/schema metadata
✓ explicit uncertainty and disagreement
✓ blinded human escalation path
✓ protocol amendment/versioning procedure
✓ degraded-mode policy
✓ immutable research artifacts
✓ Temporal-controlled workflow state
✓ complete audit trail
✓ transparent human-verification component suitable for Methods reporting
```

# 40. Strategic ELIS Objective

The overarching objective is:

> **ELIS should not ask one AI to judge another AI's research conclusion as the default scientific method. Instead, two independently isolated AI models should solve the same evidence-bound problem without seeing one another, their outputs should be compared deterministically, and a third independent model should adjudicate disagreements from the original evidence and protocol.**

This architecture converts model disagreement from an inconvenience into measurable research evidence.

It also creates a stronger foundation for reproducible, auditable, multi-model scientific research.

---

# 41. Recommended Adoption

ELIS should adopt the 3-Agent architecture as the default for research stages involving material scientific judgment.

Recommended immediate production target:

```text
Paper 1
```

Recommended sequence:

```text
Temporal T3 research workflow canary
        ↓
Paper 1 screening A/B/C
        ↓
Paper 1 extraction A/B/C
        ↓
evidence assessment A/B/C
        ↓
claim construction A/B/C
        ↓
synthesis A/B/C
        ↓
Paper 1 accepted evidence baseline
        ↓
Paper 1 drafting and final validation
```

This should become a defining methodological feature of ELIS Research.

---

# 42. Epistemic Controls

The 3-Agent control plane is not sufficient by itself. ELIS must empirically measure whether independent model agreement and adjudication are reliable.

## 42.1 Human-Reference Calibration Set

Before production Paper 1 screening, create a human-reference calibration set using qualified reviewers and an explicit disagreement-resolution process.

The calibration set should test:

- protocol clarity;
- inclusion/exclusion criteria;
- output schema;
- A accuracy;
- B accuracy;
- A/B agreement;
- criterion-level disagreement;
- C adjudication accuracy;
- C order sensitivity.

The sample size should be justified by risk, prevalence, and desired precision rather than hard-coded universally.

Material changes to:

```text
model version
system/task prompt
protocol
schema
retrieval representation
```

must trigger recalibration or a documented equivalence assessment.

## 42.2 False-Agreement Audit

A/B agreement is not proof of truth.

For any stage where A/B agreement can directly create an authoritative result, ELIS must verify a pre-specified random or stratified sample of the agreed set with human review.

The workflow should calculate:

```text
FALSE_AGREEMENT_RATE
confidence interval / uncertainty estimate
stage
criterion
model pair
protocol version
```

The protocol should define actions if the estimated error exceeds the accepted threshold.

For stages where Agent C always adjudicates every item, agreed-set sampling remains useful for producer reliability but is not a substitute for C.

## 42.3 Agreement Statistics

Report:

```text
raw observed agreement
positive agreement
negative agreement
Cohen's kappa
Gwet's AC1
prevalence / marginal distributions
```

where applicable.

Kappa and AC1 must be interpreted as complementary measures with different properties, not as interchangeable substitutes.

Criterion-level statistics should be preferred where the protocol decision is criterion-based.

## 42.4 Adjudicator C Bias Controls

Before C receives results:

- remove A/B identity;
- present them as `Result 1` and `Result 2`;
- randomize presentation order per item;
- normalize schema/formatting so model identity and verbosity cues are minimized;
- hide self-reported confidence from the adjudicative decision unless a separate calibration policy explicitly permits it.

On a pre-specified audit sample, repeat C adjudication with the order swapped.

Record:

```text
C_ORDER_SWAP_FLIP_RATE
C_ACCEPT_A_RATE
C_ACCEPT_B_RATE
C_SYNTHESIS_RATE
```

Alarm and pause thresholds should be established from the calibration pilot and frozen before production.

## 42.5 Protocol Amendment and Invalidation

Every research decision must carry:

```text
protocol_version
protocol_sha256
```

Protocol amendments must create a new immutable version and amendment record.

Each amendment must be classified:

```text
EDITORIAL_NON_DECISIONAL
CLARIFICATION
DECISION_AFFECTING
```

For a decision-affecting amendment, ELIS must perform impact analysis and identify which prior artifacts or decisions are invalid under the new protocol.

Affected items must be reprocessed or explicitly grandfathered by human scientific governance with rationale.

The amendment log should record:

```text
old protocol hash
new protocol hash
reason
approver
effective stage
affected artifacts
reprocessing decision
```

An in-flight protocol must never be silently overwritten.

## 42.6 Degraded-Mode Policy

If A or B fails terminally:

```text
DUAL_PRODUCTION_COMPLETE=FALSE
DEGRADED_MODE=TRUE
```

The normal authoritative path must stop.

Permitted next actions:

```text
retry with same approved model under retry policy
replace failed producer with an approved independent model family
human adjudication
PO/scientific-governance decision
```

A single-producer output may be retained for diagnostics or exploratory analysis but must not receive the normal authoritative status.

## 42.7 Isolation and Shared-State Controls

Blindness requires more than hiding artifact IDs.

A and B should use:

- the same immutable input snapshot;
- read-only evidence access;
- independent session state;
- no shared mutable scratch directory;
- no mutable retrieval index between runs;
- no task-specific persistent memory transfer;
- no cross-producer output lookup.

Parallel execution is desirable but not mandatory. Sequential execution is valid if the environment is order-independent and the frozen input and shared-state invariants are preserved.

Provider-side prompt or response caching should be disabled when feasible or recorded when exposed by the provider. Different providers are preferred when they materially reduce shared implementation dependencies.

Retry attempts must preserve frozen input identity and explicit attempt lineage.

## 42.8 Blinded Human Escalation

For escalated cases, the human should make a provisional decision from:

```text
evidence
protocol
anonymized A result
anonymized B result
deterministic comparison
```

before C's verdict is revealed.

The workflow should record whether the human provisional result agrees with or overturns C.

This creates an empirical control on adjudicator quality.

---

# 43. Schema Contracts

Deterministic comparison requires frozen per-stage schema contracts.

## 43.1 Producer Vocabularies

Every stage must define the exact allowed producer output vocabulary before production.

Example screening vocabulary:

```text
decision:
  INCLUDE
  EXCLUDE
  UNCERTAIN

criterion_state:
  SATISFIED
  NOT_SATISFIED
  NOT_APPLICABLE
  INSUFFICIENT_INFORMATION
```

Example claim-support vocabulary:

```text
SUPPORTED
SUPPORTED_WITH_LIMITATION
NOT_SUPPORTED
INSUFFICIENT_EVIDENCE
```

Self-reported confidence may be recorded as metadata but must not influence deterministic policy unless separately calibrated.

## 43.2 Field Comparison Classes

Every authoritative extraction field must declare one comparison class:

```text
CLOSED_VOCABULARY
ONTOLOGY_BOUND
NUMERIC
SET_VALUED
EVIDENCE_REFERENCE
FREE_TEXT_NONAUTHORITATIVE
```

Comparison behavior:

### CLOSED_VOCABULARY

Exact canonical-value equality.

### ONTOLOGY_BOUND

Canonical ontology-ID equality after deterministic normalization.

### NUMERIC

Unit normalization plus a frozen tolerance/equality rule.

### SET_VALUED

Exact or pre-declared set relationship.

### EVIDENCE_REFERENCE

Stable evidence-ID equality or set comparison.

### FREE_TEXT_NONAUTHORITATIVE

Not included in deterministic semantic agreement. Used as explanation or routed to adjudication through associated structured fields/evidence IDs.

## 43.3 Null and Missingness Semantics

Raw `null` must not carry multiple meanings.

Use explicit statuses:

```text
REPORTED
NOT_REPORTED
NOT_APPLICABLE
UNABLE_TO_EXTRACT
UNKNOWN
```

The comparator must distinguish:

```text
A says NOT_REPORTED
B says UNABLE_TO_EXTRACT
```

from:

```text
A and B both say NOT_REPORTED
```

## 43.4 Agreement Classes

Use a common agreement taxonomy across stages:

```text
EXACT
OUTCOME_ONLY
PARTIAL_FIELDS
DISAGREEMENT
SCHEMA_ERROR
```

Stage policy may add more specific subtypes but must map back to these common classes.

## 43.5 Evidence Linkage Contract

Every authoritative research element must carry resolvable evidence support.

Required fields:

```text
artifact_id
claim_or_field_id
evidence_ids[]
protocol_sha256
input_snapshot_sha256
```

A deterministic validator must reject:

```text
unknown evidence IDs
zero-support authoritative claims
evidence outside frozen snapshot
schema-invalid linkage
```

## 43.6 Draft Linkage Contract

Every substantive draft paragraph or sentence group should link to accepted `claim_id` values in the archival/source representation.

The publication renderer may hide internal IDs, but the reproducible research artifact must retain them.

---

# 44. Paper 1 Human Verification Policy

Paper 1 should explicitly include a human scientific-verification component rather than present the pipeline as fully autonomous.

Minimum human roles:

```text
1. create/adjudicate the calibration reference set;
2. audit a pre-specified sample of agreed A/B decisions where agreement creates authority;
3. adjudicate protocol ambiguities and unresolved high-risk cases;
4. review high-impact claims and final scientific conclusions;
5. approve protocol amendments;
6. perform final scientific/governance acceptance.
```

This does not replace the 3-Agent methodology.

It provides an external reference against which the model system can be evaluated and makes the methodology easier to defend in peer review.

The Paper 1 Methods section should transparently report:

- which stages were AI-only;
- which stages used mandatory C;
- which stages used human agreed-set auditing;
- calibration-set design;
- agreement statistics;
- false-agreement estimate;
- model identities/families;
- C order-randomization and flip-rate method;
- protocol amendments;
- human escalation counts;
- degraded-mode events.

The objective is not to claim that three models guarantee truth.

The objective is to create a measurable, auditable system in which independent model judgments, correlated errors, adjudicator bias, human verification, and uncertainty are all observable.
