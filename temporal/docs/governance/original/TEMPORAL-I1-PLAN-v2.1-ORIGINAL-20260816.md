# ELIS Temporal Orchestration Implementation Plan for Claude CLI

**Version:** v2.1  
**Date:** August 16, 2026  
**Program:** ELIS — Electoral Integrity Strategies  
**Initiative:** TEMPORAL-I1 — ELIS Temporal Orchestration Implementation  
**Primary implementer:** Claude CLI  
**Orchestrator:** ELIS PM  
**Independent validator:** ELIS Advisor  
**Privileged host operator:** ELIS Supervisor  
**GitHub mutation authority:** ELIS GitHub  
**PO:** Carlos Rocha  
**Status:** PO implementation directive — Temporal selected as target orchestration architecture; implementation is built in its permanent home and promoted to production after ELIS-specific validation and separate PO authority gate  
**Supersedes:** `ELIS_Temporal_Orchestration_Implementation_Plan_for_Claude_v2.0_2026-08-16.md`

---

## 1. Executive Decision

ELIS has selected **Temporal as the target authoritative durable execution-orchestration and workflow-policy engine**.

Hermes remains the **ELIS agent runtime**.

The objective is no longer to prove whether Temporal is a credible workflow platform. Generic Temporal capabilities such as durable Workflow state, Event History, Activity retries, timers, Workflow IDs, Task Queues, Signals/Updates, replay, and long-running Workflow support are treated as trusted platform dependencies.

The engineering question is now:

> **Can ELIS be implemented correctly, securely, and maintainably on Temporal so that Temporal owns durable orchestration while Hermes remains a replaceable agent-execution runtime?**

Target architecture:

```text
PO / User
    │
    ▼
Temporal
AUTHORITATIVE ELIS WORKFLOW / EXECUTION STATE
    │
    ├── ELIS Ideas
    ├── ELIS PM
    ├── ELIS Research
    ├── ELIS Advisor
    ├── ELIS Supervisor
    └── ELIS GitHub
             │
             ▼
       Hermes agent runtime

GitHub
= source-code and versioned artifact system of record

Kanban
= transitional execution/tracking layer;
  after cutover, optional human-facing projection of Temporal state

Omnigent
= optional supervision/harness layer
```

Architectural split:

```text
Temporal Workflow code
= deterministic orchestration policy

Temporal Activities
= non-deterministic work and side effects

Hermes
= AI-agent runtime behind an ELIS adapter

ELIS policy
= role authority, validation separation, capability rules,
  workflow identity, evidence semantics, and approval gates
```

ELIS should stop adding new general-purpose workflow-engine functionality to Hermes except for bounded migration-safety fixes required before Temporal cutover.

### 1.1 Permanent ELIS Temporal Home

The permanent implementation location is:

```text
/home/samurai/temporal/
```

This is **not** a disposable pilot directory. Code, configuration, schemas, tests, deployment artifacts, logs, evidence, and operational documentation are built in this final location from the beginning.

The implementation lifecycle is:

```text
/home/samurai/temporal/
        ↓
pre-authoritative implementation
        ↓
ELIS-specific validation
        ↓
service/persistence hardening
        ↓
PO production-authority gate
        ↓
same ELIS Temporal implementation becomes production-authoritative
```

There must be no unnecessary `/temporal-pilot/ → /temporal/` application migration later.

The existing discovery files under:

```text
/home/samurai/temporal-pilot/
```

are **discovery inputs only**. Claude should reconcile/copy their useful content into the permanent `/home/samurai/temporal/` documentation/artifact structure and then treat `/home/samurai/temporal/` as authoritative.

### 1.2 Cognitive Orchestration vs Durable Execution Orchestration

Use precise terminology:

```text
Cognitive orchestration
= Hermes/LLM reasoning:
  analyze
  propose decomposition
  classify
  recommend
  choose strategy

Durable execution orchestration
= Temporal:
  persist the recorded decision
  validate it against ELIS policy
  deduplicate
  sequence dependencies
  dispatch authorized Activities
  enforce profile/authority rules
  enforce gates
  wait for PO
  retry/reconcile
  maintain workflow history
```

Temporal does **not** make LLM reasoning deterministic.

The governing pattern is:

```text
Temporal Workflow
        ↓
Hermes/LLM Activity
        ↓
structured decision/result
        ↓
Temporal persists the Activity result
        ↓
deterministic ELIS Workflow policy governs what may happen next
```

Therefore the authoritative architectural statement is:

> **Temporal owns authoritative durable execution orchestration and workflow policy for ELIS; Hermes/LLM Activities perform non-deterministic cognitive work.**

---

## 2. What Claude Should Not Re-Prove

Do not spend ELIS engineering time creating tests whose purpose is merely to prove that Temporal itself supports:

- Durable Workflow persistence.
- Event-history replay.
- Generic worker restart recovery.
- Activity retry infrastructure.
- Timers.
- Workflow IDs.
- Parent/child Workflow mechanics.
- Signals/Updates.
- Task Queue fundamentals.
- Generic long-running Workflow operation.
- Generic production viability.

Validate **ELIS use of those primitives**, not Temporal as a product.

Examples:

```text
Trusted Temporal primitive:
Durable Workflow state

ELIS validation:
Did the PO gate wait for the correct authority and advance only
after the correct ELIS decision?
```

```text
Trusted Temporal primitive:
Activity result persisted in Workflow history

ELIS validation:
Did Hermes/LLM reasoning execute as an Activity and did Workflow
code consume the recorded structured result correctly?
```

---

## 3. Primary Objectives

TEMPORAL-I1 must implement ELIS so that:

1. Temporal can own ELIS durable workflow state.
2. Hermes is accessed through a narrow stable Adapter.
3. All six ELIS profiles are explicitly routed.
4. `assigned_profile = execution_profile = expected security principal`.
5. Required capabilities are checked before expensive agent execution.
6. ELIS authority boundaries are structurally enforced.
7. Duplicate logical executions are prevented through semantic Workflow identity.
8. Shared-profile concurrency policies are deterministic.
9. Implementer → preflight → independent validator ordering is structural.
10. PO gates are explicit and durable.
11. LLM decisions occur in Activities; deterministic Workflow code governs their recorded consequences.
12. External side effects use explicit idempotency/reconciliation.
13. Existing Hermes/Kanban history is preserved.
14. Migration avoids split-brain authority.
15. Future Hermes upgrades primarily require Adapter compatibility rather than reapplying an ELIS workflow-engine patch stack.

---

## 4. Existing Hermes P2 Branch

Current reported P2 state:

```text
Branch: orchestration-remediation-20260815
Commits: 13 total
HEAD: ac6d2ca4bb
Deployment: none
Independent review: pending
```

Claude's Hermes P2 remediation is retained as:

1. **Transitional safety stabilization** for the current Kanban runtime.
2. **ELIS invariant specification** for the Temporal implementation.
3. **Regression source** for migration.

The P2 branch should now move to independent review in parallel with TEMPORAL-I1.

Do not begin another broad Hermes hardening cycle unless a bounded defect is blocking safe migration and PO separately authorizes the correction.

The long-term objective is to remove durable orchestration authority from Hermes, not to perfect a permanent ELIS-specific Hermes workflow engine.

---

## 5. Governance

### ELIS PM

Owns TEMPORAL-I1 orchestration.

- Creates the authoritative task graph.
- Maintains phase/gate dependencies.
- Routes Claude implementation work.
- Routes root operations to ELIS Supervisor.
- Routes GitHub mutations to ELIS GitHub.
- Routes validation to ELIS Advisor.
- Performs deterministic completeness preflight.
- Reports gates to PO.
- Does not implement Temporal software.

### Claude CLI

Primary technical implementer.

- Designs and implements the ELIS Temporal integration.
- Builds Hermes Adapter v1.
- Builds Workflows and Activities.
- Implements six-profile routing.
- Implements ELIS workflow policies.
- Implements capability admission.
- Implements idempotency/reconciliation.
- Implements migration/projection tooling.
- Implements ELIS-specific tests.
- Produces host-application packets.
- Reports residual gaps.
- Does not self-certify readiness.

### ELIS Supervisor

Privileged host/runtime operator.

- Applies only PO-authorized root/systemd/network/service changes.
- Executes Claude host packets.
- Verifies host state.
- Does not independently redesign the Temporal architecture unless a security or compatibility defect requires escalation.

### ELIS Advisor

Independent validator.

- Validates architecture, routing, authority, security, integration, and migration readiness.
- Does not implement.

### ELIS GitHub

Sole GitHub mutation authority.

- Feature-branch push.
- Draft PR creation.
- Authorized PR updates/read-back.
- No merge, protected-branch mutation, repository administration, or secrets changes without separate authority.

### ELIS Research

Continues research work independently and may supply representative workflows. It is not the Temporal platform implementer.

### ELIS Ideas

Optional architecture/ideas input only.

---

## 6. Kanban Tracking

Claude should **not autonomously create the authoritative TEMPORAL-I1 Kanban graph**.

Claude should produce:

`TEMPORAL-I1-TASK-MANIFEST.yaml`

with:

```yaml
task_key:
title:
phase:
purpose:
implementer:
validator:
parents:
required_capabilities:
decomposable:
expected_artifacts:
acceptance_checks:
stop_conditions:
root_required:
github_mutation_required:
```

ELIS PM reviews the manifest and creates each authoritative task once.

Recommended chain:

```text
TEMPORAL-I1 ROOT
│
├── T0A — Architecture/environment reconciliation
├── T0B — Isolated Temporal installation
├── T0P — PM deterministic foundation preflight
├── T0V — Advisor foundation validation
│
├── T1A — Hermes Adapter v1
├── T1B — Six-profile routing/workers
├── T1C — Execution-principal/capability model
├── T1P — PM deterministic T1 preflight
├── T1V — Advisor routing/security validation
│
├── T2A — ELIS workflow primitives
├── T2B — LLM decision/activity integration
├── T2C — External side-effect idempotency
├── T2P — PM deterministic T2 preflight
├── T2V — Advisor workflow-policy validation
│
├── T3A — Representative ELIS workflows
├── T3B — ELIS integration/regression suite
├── T3P — PM deterministic T3 preflight
├── T3V — Advisor integration validation
│
├── T4A — Migration/projection implementation
├── T4B — Cutover/rollback package
├── T4P — PM deterministic T4 preflight
├── T4V — Advisor migration-readiness validation
│
└── T5R — First authoritative Temporal workflow readiness
    └── separate PO cutover decision
```

Do not create one card per minor coding operation.

---

## 7. Permanent Filesystem and Repository Boundary

The permanent host location is:

```text
/home/samurai/temporal/
```

Recommended host layout:

```text
/home/samurai/temporal/
├── bin/                 # pinned Temporal CLI/server binaries if locally managed
├── app/                 # ELIS Temporal application source/worktree
├── config/              # Temporal + ELIS runtime configuration
├── state/               # pre-authoritative local Temporal persistence only
├── logs/
├── artifacts/
├── deployment/
├── tests/
├── backups/
└── docs/
```

Inside `app/`, keep Temporal integration isolated from Hermes upstream source. Preferred logical application structure:

```text
app/
├── README.md
├── pyproject.toml
├── src/elis_temporal/
│   ├── workflows/
│   ├── activities/
│   ├── workers/
│   ├── adapter/hermes/
│   ├── policies/
│   ├── profiles/
│   ├── approvals/
│   ├── capabilities/
│   ├── idempotency/
│   ├── projection/
│   └── provenance/
└── tests/
    ├── unit/
    ├── integration/
    ├── security/
    ├── migration/
    └── historical_failures/
```

Claude should inspect existing ELIS repositories and recommend whether `app/` should ultimately map to:

- a new `elis-temporal` repository; or
- a clearly isolated module in an existing ELIS Core repository.

Do not create a public repository without PO approval.

The objective is:

> **Temporal integration code must not become another patch stack embedded in Hermes.**

No application path, schema, Workflow-ID convention, Adapter contract, or operational convention should be knowingly designed as disposable pilot-only structure unless explicitly marked as a test fixture.

---

## 8. T0 — Permanent-Home Temporal Foundation

T0 is implementation, not a technology feasibility study.

### 8.1 Reuse Existing Discovery

Reuse the completed Claude discovery where still current:

```text
CPU: 8
Available RAM for practical planning: ~10 GB
Free disk: ~126 GB
Temporal gRPC port 7233: available
Temporal Web UI port 8233: available
```

Existing discovery inputs:

```text
/home/samurai/temporal-pilot/
```

Claude should reconcile those documents into:

```text
/home/samurai/temporal/docs/
/home/samurai/temporal/artifacts/
```

Do not repeat discovery unnecessarily.

### 8.2 Chosen Lightweight Pre-Authoritative Configuration

For implementation and ELIS integration work, use the **Temporal CLI single-binary development server with file-backed SQLite persistence**, not Docker Compose.

Rationale:

- no Docker daemon;
- no Elasticsearch;
- no Cassandra;
- no Kubernetes;
- no container memory overhead;
- no root requirement merely to start Temporal;
- bundled Web UI;
- adequate for ELIS integration development on the measured server hardware.

Target configuration:

```text
Temporal home:      /home/samurai/temporal/
Temporal address:   127.0.0.1:7233
Temporal UI:        127.0.0.1:8233
Persistence:        file-backed SQLite
SQLite file:        /home/samurai/temporal/state/temporal.db
ELIS Namespace:     elis
Network exposure:   loopback by default
Docker:             no
Elasticsearch:      no
Kubernetes:         no
```

Use the installed Temporal CLI version's exact supported syntax. Conceptually:

```bash
temporal server start-dev   --db-filename /home/samurai/temporal/state/temporal.db
```

The default local Temporal address is expected to remain `localhost:7233` and the bundled UI `localhost:8233`; Claude must verify the exact flags and resulting bind addresses for the installed CLI before formalizing service files.

Create/use a dedicated `elis` Namespace rather than treating the default learning Namespace as the long-term ELIS namespace.

### 8.3 Resource Discipline

The initial configuration must remain lightweight enough to coexist with the six live Hermes gateways.

Required operating principles:

- no Docker daemon solely for Temporal;
- no Elasticsearch;
- no HA replicas;
- no Kubernetes;
- no unnecessary auxiliary services;
- loopback-only server/UI unless PO later authorizes broader access;
- logs rotated;
- state/backups kept under `/home/samurai/temporal/`;
- workers started only as needed during implementation;
- measure actual memory/CPU under representative ELIS load before production authority.

Do not invent hard memory limits before measurement. Record observed idle and representative-load resource use.

### 8.4 Production Promotion — Same Implementation, Hardened Service Topology

Once the ELIS Temporal implementation is functioning correctly and passes the required ELIS-specific validation gates, **the same `/home/samurai/temporal/` implementation is promoted toward production**.

There is no second application tree and no rewrite.

However, `temporal server start-dev` remains a development-mode server. Before Temporal becomes production-authoritative, harden the service topology while preserving the same:

- application code;
- Workflow definitions;
- Activity contracts;
- Adapter;
- task-queue/profile model;
- namespace semantics;
- configuration model;
- filesystem home.

Chosen lightweight production target for `elis-server`:

```text
Deployment:         single-node self-hosted Temporal
Temporal services:  co-located on elis-server
Persistence:        PostgreSQL SQL persistence
Visibility:         PostgreSQL SQL visibility
Elasticsearch:      no
Docker/Kubernetes:  no, unless a later operational decision changes this
UI:                 optional; local/private only
HA replicas:        no initially
Application home:   /home/samurai/temporal/
```

Use PostgreSQL for the production-authoritative Temporal state rather than promoting the file-backed `start-dev` SQLite database as the long-term production datastore.

If a suitable local PostgreSQL instance already exists and can be safely isolated, prefer dedicated Temporal databases/users there. Otherwise Claude must prepare a root-required host packet for ELIS Supervisor to install/configure the smallest appropriate local PostgreSQL deployment after measuring headroom.

The pre-authoritative SQLite Workflow histories are implementation/test history and do not need to become the production-authoritative cluster history. Production authority begins only after the hardened service/persistence topology is validated and PO authorizes cutover.

Thus the promotion model is:

```text
same code + same /home/samurai/temporal/ home
        ↓
replace development Temporal service/persistence with hardened single-node service
        ↓
re-run ELIS integration checks
        ↓
Advisor validation
        ↓
PO production-authority gate
```

This is an **authority/service hardening promotion**, not an application migration.

### 8.5 T0 Deliverables

Claude produces/updates:

```text
/home/samurai/temporal/docs/TEMPORAL-I1-ARCHITECTURE.md
/home/samurai/temporal/docs/TEMPORAL-I1-ENVIRONMENT-DELTA.md
/home/samurai/temporal/docs/TEMPORAL-I1-HOST-PREREQUISITES.md
/home/samurai/temporal/artifacts/TEMPORAL-I1-TASK-MANIFEST.yaml
/home/samurai/temporal/deployment/start-dev/
```

The deployment package must include:

- pinned Temporal CLI version;
- checksum/source record;
- start command/wrapper;
- stop command;
- health check;
- Namespace initialization;
- log handling;
- SQLite backup procedure;
- rollback/removal procedure.

### 8.6 T0 Validation Scope

Advisor validates ELIS-specific boundary correctness:

- permanent `/home/samurai/temporal/` structure established;
- Temporal is still non-authoritative;
- Hermes remains agent runtime;
- no Temporal integration is embedded as a Hermes fork;
- no unnecessary Docker/Elasticsearch/HA stack;
- no credential/security regression;
- rollback is defined;
- production-promotion design is documented;
- no production authority was silently granted.

Advisor does not need to prove Temporal's generic Workflow-engine functionality.

Required verdict:

```text
PASS + NO_UNRESOLVED_TEMPORAL_ELIS_FOUNDATION_DEFECT
```

---

## 9. T1 — Hermes Adapter and Six ELIS Profiles

### Hermes Adapter v1

Define a stable interface conceptually equivalent to:

```python
run_agent(
    profile,
    execution_id,
    instructions,
    input_artifacts,
    required_capabilities,
    execution_context,
    correlation_id,
)
```

Result:

```text
status
structured_result
evidence_refs
checkpoint
usage
failure_class
runtime_identity
capability_result
correlation_id
```

The Adapter should provide:

- Profile selection.
- Runtime identity observation.
- Structured input/output.
- Timeout/cancellation behavior.
- Evidence/artifact references.
- Checkpoint references.
- Capability result.
- Failure classification.

Temporal must not depend on Hermes Kanban internals for durable orchestration.

### Six Profiles

Implement explicit Temporal routing for:

- ELIS Ideas
- ELIS PM
- ELIS Research
- ELIS Advisor
- ELIS Supervisor
- ELIS GitHub

For each define:

```text
Temporal Task Queue
Hermes profile
worker process
expected gateway/service
expected OS/security principal
allowed Activity classes
prohibited Activity classes
concurrency policy
capability classes
```

### Execution-Context Fidelity

Required invariant:

```text
assigned_profile
=
execution_profile
=
expected security principal
```

For GitHub:

```text
ELIS GitHub Activity
→ ELIS GitHub Task Queue
→ ELIS GitHub Worker
→ correct service/cgroup/security principal
→ gh-agentd
```

A mismatch must block before external mutation.

Do not route an entire multi-profile board under the GitHub principal.

### Capability Admission

Before an expensive Hermes/LLM Activity:

```text
requirements
→ profile/runtime
→ required capabilities
→ credential/provider state
→ ALLOW or WAITING_FOR_CAPABILITY
```

Negative checks must include:

- No personal GitHub fallback.
- No main push unless explicitly authorized.
- No merge without PO.
- No root capability for ordinary profiles.

Required T1 verdict:

`PASS + NO_UNRESOLVED_AGENT_ROUTING_OR_SECURITY_PRINCIPAL_DEFECT`

---

## 10. T2 — ELIS Workflow and Authority Primitives

### Semantic Workflow Identity

Define deterministic IDs such as:

```text
ELIS/<domain>/<process>/<semantic-key>
```

Requirements:

- Equivalent logical starts resolve to one canonical open execution where appropriate.
- Legitimately distinct work remains distinct.
- Retry/restart does not create a second logical execution.

### LLM Decisions as Activities

Pattern:

```text
Temporal Workflow
    ↓
Hermes/LLM Activity
"analyze / plan / decompose / classify"
    ↓
structured result
    ↓
Temporal records result
    ↓
Workflow applies deterministic ELIS policy
    ↓
schedule / reject / gate / wait / validate / continue
```

The LLM reasoning is non-deterministic cognitive work.

Temporal owns durable execution orchestration: the Activity result is recorded, then deterministic ELIS Workflow policy governs its execution consequences.

### LLM-Proposed Decomposition

Use a structured result such as:

```yaml
decision_id:
parent_execution_id:
proposed_children:
  - semantic_key:
    role:
    purpose:
    required_capabilities:
    dependencies:
    decomposable:
rationale:
```

Workflow code validates:

- Role allowed.
- No self-validation.
- No duplicate semantic execution.
- Legal dependencies.
- Registered capability classes.
- Policy limits.

The LLM proposes. Temporal decides whether the proposal may become executable work.

### Implementation → Preflight → Validation

Reusable pattern:

```text
Implementation
    ↓
Deterministic completeness preflight
    ↓
Independent validation
    ↓
Next gate
```

Required:

- Advisor cannot run before preflight PASS.
- Implementer cannot satisfy validation.
- Parent completion cannot override a separate explicit gate/wait.
- Validation verdict remains distinct from execution state.

### PO Approval

Implement durable state such as:

`WAITING_FOR_PO`

Approval must:

- Name the Workflow/gate.
- Be durably recorded.
- Be required only where ELIS policy requires it.
- Never be inferred from unrelated actions.

### Profile Concurrency

Implement ELIS shared-specialist policy using Temporal-native mechanisms.

Examples:

- One active ELIS Supervisor execution globally where required.
- Configurable Advisor concurrency.
- Different profiles allowed concurrently.

Avoid unnecessary global serialization.

### Notifications

START/SUMMARY/decision notifications are lightweight Activities/events, not full AI orchestration tasks unless AI generation is genuinely needed.

### Evidence

Temporal history owns orchestration/control-state provenance.

Immutable ELIS evidence artifacts continue to own:

- Implementation evidence.
- Validation evidence.
- Security evidence.
- Scientific evidence.
- Host-operation evidence.

Preserve:

> **Evidence is immutable. Current authority/control state may evolve separately.**

Required T2 verdict:

`PASS + NO_UNRESOLVED_ELIS_WORKFLOW_POLICY_DEFECT`

---

## 11. External Side-Effect Idempotency

For every mutating Activity define:

```text
operation_id
target
desired_state
read_before_write
write
read_after_write
reconciliation
retry_behavior
```

### GitHub

Use deterministic branch/operation identity.

Before creating a PR:

- Check for an existing equivalent PR.
- Reuse/update when semantically identical.
- Never create duplicate PRs because acknowledgment was lost.

### Discord

Use notification identity where duplicate suppression matters.

Discord is never execution authority.

### Files/Artifacts

Use deterministic paths/content hashes where appropriate.

Keep historical evidence immutable.

### Host Operations

Root-required operations require explicit host packets and PO/Supervisor authority.

Temporal may orchestrate the wait but does not grant privilege to an unprivileged worker.

---

## 12. T3 — Representative ELIS Workflows

Implement real ELIS patterns rather than generic demos.

### Core workflow

```text
PO / ELIS PM
→ implementation
→ deterministic preflight
→ ELIS Advisor validation
→ PO gate where required
→ next stage
```

### Research workflow

```text
PO
→ ELIS Research
→ research/specialist work
→ completeness check
→ Advisor validation where required
→ research gate
```

Do not migrate an active Gate B workflow mid-flight.

### GitHub publication workflow

```text
approved change packet
→ capability preflight
→ ELIS GitHub Activity
→ feature branch / draft PR
→ read-back verification
→ validation
→ PO merge decision
```

No direct protected-branch mutation.

---

## 13. T3 — ELIS Integration Tests

Validate ELIS implementation, not Temporal itself.

At minimum test:

1. **Duplicate logical start** — same semantic key yields one canonical Workflow.
2. **Cross-domain shared profile** — Core and Research request Supervisor; configured policy holds.
3. **Different profiles** — legitimate concurrency remains possible.
4. **Preflight/validation gate** — Advisor cannot start early.
5. **Self-validation attempt** — rejected.
6. **LLM decomposition result** — structured result is validated before children execute.
7. **Wrong execution principal** — blocks before mutation.
8. **Missing capability** — `WAITING_FOR_CAPABILITY` before expensive Hermes execution.
9. **Ambiguous GitHub retry** — reconcile/reuse, no duplicate PR.
10. **PO gate** — privileged action waits for PO.
11. **Notification** — no full AI worker for routine reporting.
12. **Hermes failure mapping** — timeout/provider failure/block mapped correctly.
13. **Historical duplicate-card scenario** — no duplicate logical Workflow.
14. **Historical blocked-validator scenario** — no premature validation.

Required T3 verdict:

`PASS + NO_UNRESOLVED_ELIS_TEMPORAL_INTEGRATION_DEFECT`

---

## 14. T4 — Migration and Kanban Projection

### Transitional state

Until cutover:

```text
Hermes Kanban
= current production authority

Temporal
= permanent-home pre-authoritative implementation / selected new workflows as authorized
```

Do not make the same logical workflow authoritative in both systems.

### Target state

After cutover:

```text
Temporal
= authoritative execution state

Kanban
= optional projection
```

If retained:

```text
Temporal RUNNING
→ Kanban RUNNING

Temporal WAITING_FOR_PO
→ Kanban BLOCKED / WAITING FOR PO

Temporal WAITING_FOR_CAPABILITY
→ Kanban BLOCKED / CAPABILITY

Temporal COMPLETED
→ Kanban DONE
```

Authority direction:

`Temporal → Kanban`

Any user action originating in a Kanban/UI must become a validated Temporal command/signal/update.

### Historical preservation

Keep historical Hermes/Kanban execution provenance intact.

Do not rewrite it as Temporal history.

Required T4 verdict:

`PASS + NO_UNRESOLVED_TEMPORAL_MIGRATION_AUTHORITY_DEFECT`

---

## 15. Hermes Upgrade Independence

Create:

- `HERMES-ADAPTER-CONTRACT.md`
- `HERMES-PATCH-TO-TEMPORAL-MIGRATION-MATRIX.md`

For each current Hermes orchestration patch record:

```text
patch/invariant
current owner
future Temporal/Adapter owner
needed during migration?
needed after cutover?
removal condition
upstream contribution candidate?
```

Target future Hermes upgrade workflow:

```text
New Hermes release
→ update/install runtime
→ run Adapter contract tests
→ run six-profile canaries
→ update Adapter only if needed
```

Avoid reapplying custom ELIS workflow-state machinery once Temporal owns that function.

---

## 16. Host-Root Change Policy

Claude may design but not apply unauthorized root changes.

Each privileged change requires:

`TEMPORAL-HOST-APPLICATION-PACKET-<ID>.md`

with:

- Purpose.
- Existing state.
- Target state.
- Exact commands.
- Files/services changed.
- Positive tests.
- Negative tests.
- Rollback.
- Blast radius.
- Security impact.
- Idempotency.
- Stop conditions.

Authority chain:

```text
Claude host packet
→ PO authorization
→ ELIS Supervisor applies
→ PM deterministic verification
→ Advisor validation where material
```

---

## 17. Current Gate-B GitHub Blocker

The current `gh-agentd`/execution-context blocker remains separate live work.

Temporal's durable target must be:

```text
ELIS GitHub Activity
→ ELIS GitHub worker
→ correct service/cgroup/security principal
→ gh-agentd
```

Do not install a board-wide GitHub execution identity merely to unblock one board.

Before PO applies the existing Option-A host packet, identify whether it conflicts with per-profile Temporal routing.

In particular, reject any design that makes `hermes-gateway-elis-github.service` the security/execution owner for the entire `elis-research` board if that would cause non-GitHub assignees to inherit the GitHub principal.

The durable invariant is per assigned profile, not per board:

```text
assigned ELIS GitHub work
→ ELIS GitHub worker/principal

assigned ELIS Advisor work
→ ELIS Advisor worker/principal

assigned ELIS Supervisor work
→ ELIS Supervisor worker/principal

assigned ELIS Research work
→ ELIS Research worker/principal
```

Do not create a competing credential-routing mechanism without reconciliation.

---

## 18. Parallel Work

The following may continue in parallel:

- ELIS Research Gate B where not blocked.
- Independent review of the Hermes P2 branch.
- TEMPORAL-I1 implementation in the permanent `/home/samurai/temporal/` home, using an isolated source worktree/repository where appropriate.

Do not let Claude Temporal work mutate the live Hermes P2 branch or live Kanban databases.

---

## 19. Required Claude Deliverables

Claude must produce:

1. `TEMPORAL-I1-TASK-MANIFEST.yaml`
2. `TEMPORAL-I1-ARCHITECTURE.md`
3. `TEMPORAL-I1-ENVIRONMENT-DELTA.md`
4. `TEMPORAL-I1-HOST-PREREQUISITES.md`
5. Lightweight pre-authoritative Temporal deployment definition under `/home/samurai/temporal/deployment/start-dev/`.
6. Hermes Adapter v1.
7. `HERMES-ADAPTER-CONTRACT.md`
8. Six-profile routing map.
9. Execution-principal policy.
10. Capability-preflight implementation.
11. Semantic Workflow-ID policy.
12. LLM-Activity / deterministic-Workflow pattern.
13. Structured decomposition schema/policy.
14. Implementer/preflight/validator primitive.
15. PO approval primitive.
16. Profile-concurrency policy.
17. Notification model.
18. External-side-effect idempotency policy.
19. Representative Core workflow.
20. Representative Research workflow.
21. GitHub publication workflow.
22. ELIS integration/security test suite.
23. Kanban migration/projection design.
24. `HERMES-PATCH-TO-TEMPORAL-MIGRATION-MATRIX.md`
25. Workflow-versioning policy.
26. Security assessment.
27. Operations/cutover packet.
28. Rollback packet.
29. Host application packets where required.
30. Requirement → implementation → test mapping.
31. Known residual gaps.
32. Recommended first Temporal-authoritative production workflow.

---

## 20. Production Promotion Design Constraint

Claude must design TEMPORAL-I1 so the development implementation can be promoted without restructuring application semantics.

Promotion is allowed to change:

- Temporal service binary/topology;
- persistence backend;
- service management;
- backup/restore;
- authentication/network hardening;
- operational monitoring.

Promotion must **not** require redesign of:

- Workflow IDs;
- Workflow/Activity contracts;
- Hermes Adapter API;
- six-profile routing semantics;
- ELIS authority model;
- capability schema;
- evidence/provenance schema;
- repository/application layout.

Before production authority, Claude must provide a production-hardening delta showing exactly what changes from:

```text
start-dev + file-backed SQLite
```

to:

```text
single-node self-hosted Temporal + PostgreSQL persistence/visibility
```

and demonstrate that this is an operational hardening step, not a second implementation.

---

## 21. Implementation Discipline

Claude should:

- Use small, independently revertible commits.
- Keep Temporal integration outside the Hermes fork.
- Avoid unrelated refactors.
- Use explicit schemas/contracts.
- Keep Workflow logic deterministic.
- Put LLM/tool/external calls in Activities.
- Keep role/authority rules explicit.
- Preserve least privilege.
- Preserve historical evidence.
- Report gaps rather than forcing incomplete designs.

Recommended commit groups:

```text
1. temporal foundation/package skeleton
2. hermes adapter
3. six-profile workers/routing
4. execution-principal/capability policy
5. workflow identity/authority primitives
6. llm/decomposition activity integration
7. idempotency/external side effects
8. representative workflows
9. migration/projection
10. integration/security tests
11. operations/cutover documentation
```

---

## 22. Validation Philosophy

Advisor validates **ELIS implementation correctness**, not Temporal as a product.

Focus on:

- Deterministic/non-deterministic boundary.
- Hermes Adapter correctness.
- Six-profile routing.
- Execution-principal fidelity.
- Capability admission.
- Authority separation.
- Semantic Workflow identity.
- LLM result handling.
- Decomposition policy.
- Implementer/preflight/validator ordering.
- PO gates.
- Idempotency/reconciliation.
- Kanban migration authority.
- Security.
- Rollback.
- Hermes upgrade independence.

---

## 23. Validation Gates

| Gate | Scope | Implementer | Validator | Required outcome |
|---|---|---|---|---|
| T0V | ELIS foundation/boundary | Claude + Supervisor where root required | Advisor | `PASS + NO_UNRESOLVED_TEMPORAL_ELIS_FOUNDATION_DEFECT` |
| T1V | Adapter/routing/security principal | Claude | Advisor | `PASS + NO_UNRESOLVED_AGENT_ROUTING_OR_SECURITY_PRINCIPAL_DEFECT` |
| T2V | ELIS workflow/authority primitives | Claude | Advisor | `PASS + NO_UNRESOLVED_ELIS_WORKFLOW_POLICY_DEFECT` |
| T3V | Representative workflows + integration tests | Claude | Advisor | `PASS + NO_UNRESOLVED_ELIS_TEMPORAL_INTEGRATION_DEFECT` |
| T4V | Migration/projection/cutover readiness | Claude | Advisor | `PASS + NO_UNRESOLVED_TEMPORAL_MIGRATION_AUTHORITY_DEFECT` |
| I1 Final | Full implementation readiness | Claude | Advisor | `PASS + NO_UNRESOLVED_ELIS_TEMPORAL_ARCHITECTURE_DEFECT` |
| T5 | First production-authoritative workflow | N/A | PO after Advisor | Separate PO authorization |

---

## 24. First Production-Authoritative Workflow

Claude should recommend one bounded workflow for first cutover.

Criteria:

- Low risk.
- Reversible.
- Clear start/end.
- Clear PO/Advisor boundary.
- At least two ELIS profiles.
- No destructive host change.
- Auditable evidence.
- Simple rollback.

Do not activate without explicit PO authorization.

---

## 25. Success Criteria

TEMPORAL-I1 succeeds when:

1. Temporal is installed and integrated under the permanent `/home/samurai/temporal/` home in pre-authoritative mode.
2. Hermes is invoked through a stable Adapter.
3. All six ELIS profiles have explicit routing/security expectations.
4. Capability admission occurs before expensive agent work.
5. LLM reasoning executes in Activities and Workflow code governs recorded consequences.
6. Semantic Workflow identity prevents duplicate logical execution.
7. ELIS authority boundaries are structurally encoded.
8. Implementer/preflight/validator sequencing is structural.
9. PO gates are explicit and durable.
10. External side effects are idempotent/reconcilable.
11. Representative ELIS workflows work correctly.
12. ELIS integration/security tests pass.
13. Migration avoids split-brain authority.
14. Historical provenance is preserved.
15. Hermes orchestration patch dependency can be reduced after cutover.
16. Advisor returns the required final verdict.
17. PO can make a bounded production-cutover decision.

---

## 26. Status Vocabulary

Claude must use:

```text
IMPLEMENTED
PARTIALLY IMPLEMENTED
DEFERRED
BLOCKED
NOT APPLICABLE
```

Claude must not self-declare:

```text
PRODUCTION READY
CUTOVER APPROVED
TEMPORAL AUTHORITATIVE IN PRODUCTION
```

These require Advisor validation and PO authorization.

---

## 27. Immediate Instructions to Claude

1. Treat Temporal as the selected target architecture.
2. Do not debate or re-prove generic Temporal viability.
3. Reuse completed discovery where still current.
4. Produce the updated `TEMPORAL-I1-TASK-MANIFEST.yaml`.
5. Recommend the repository boundary.
6. Establish `/home/samurai/temporal/` as the permanent home and implement the lightweight file-backed `start-dev` foundation there.
7. Implement Hermes Adapter v1.
8. Implement six-profile routing.
9. Implement execution-principal and capability admission.
10. Implement semantic Workflow identity and authority primitives.
11. Implement the LLM Activity → deterministic Workflow pattern.
12. Implement representative ELIS workflows.
13. Implement external-side-effect idempotency.
14. Implement ELIS-specific integration/security tests.
15. Implement migration/projection tooling.
16. Prepare host packets for privileged changes.
17. Stop at independent validation gates required by the authoritative PM task graph.
18. Do not perform production cutover.
19. Do not broaden Hermes P2 except for separately authorized migration-safety work.

---

## 28. Final Architectural Principle

> **Temporal owns durable orchestration. Hermes executes ELIS agents. LLM reasoning occurs in Activities. Temporal deterministically governs the recorded consequences of those decisions. ELIS policy defines authority and security. GitHub owns source and versioned artifacts. Kanban becomes transitional and ultimately derivative, not a competing execution authority.**

The objective is not to make AI reasoning deterministic.

The objective is to make **ELIS execution around AI reasoning durable, explicit, authority-controlled, idempotent, observable, and independent of Hermes Kanban internals**.

---

## 29. Authorization Boundary

This plan authorizes:

- Pre-authoritative Temporal installation and implementation in the permanent `/home/samurai/temporal/` home.
- ELIS Temporal source development.
- Hermes Adapter development.
- Six-profile routing development.
- ELIS Workflow implementation.
- ELIS-specific tests.
- Migration/projection tooling.
- Local commits.
- Host-application packet preparation.
- GitHub publication through ELIS GitHub under existing mutation controls.

This plan does **not** authorize:

- Production Temporal authority.
- Production Kanban replacement.
- Destructive board migration.
- Production gateway shutdown.
- Unreviewed root changes.
- Weakening credential isolation.
- Protected/default-branch push.
- PR merge without PO.
- Removing Hermes stabilization before Temporal cutover.
- Claude self-validation.

Authority chain:

```text
Claude implementation
→ ELIS PM deterministic completeness preflight
→ ELIS Advisor independent validation
→ PO decision
```

Root-required changes:

```text
Claude host packet
→ PO authorization
→ ELIS Supervisor application
→ PM deterministic verification
→ Advisor validation where material
```

GitHub mutations:

```text
Approved implementation packet
→ ELIS GitHub
→ feature branch / draft PR
→ validation
→ PO merge decision
```
