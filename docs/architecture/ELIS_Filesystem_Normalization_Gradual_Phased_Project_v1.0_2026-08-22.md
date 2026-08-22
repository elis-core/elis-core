# ELIS Filesystem Normalization — Gradual Phased Project

**Version:** 1.0  
**Date:** 2026-08-22  
**Status:** Work in Progress  
**Normative role:** This document is the authoritative transformation and compliance plan for moving `elis-server` from observed current state to the target architecture defined by `ELIS_Production_Infrastructure_Taxonomy_v1.0`. It must not redefine that target architecture.  
**Basis:** `ELIS_Production_Infrastructure_Taxonomy_v1.0_2026-08-22.md`  
**Scope:** `elis-server` production infrastructure normalization

---

## 1. Purpose

This project defines how `elis-server` should gradually converge to the approved ELIS Production Infrastructure Taxonomy without disrupting working production services.

The objective is not to create a cosmetically uniform filesystem. The objective is to make ELIS infrastructure predictable, auditable, maintainable, and immediately understandable to Linux developers and operators.

The target state should make it possible to determine, from Git and the server filesystem:

- which ELIS components exist;
- which components are production, support, pilot, transitional, or retired;
- which logical agents exist;
- which runtime implements each logical agent;
- where executable software is installed;
- where configuration is stored;
- where persistent state is stored;
- where logs and ephemeral state belong;
- which Unix identity owns each service;
- what the canonical Git source is;
- whether the deployed state matches the reviewed canonical state.

---

## 2. Governing Principle

The project follows this rule:

> **One logical agent identity, explicit runtime implementations, one canonical source in Git, and filesystem locations determined by operational function rather than by whichever project or migration created them.**

The server should follow standard Linux filesystem semantics first, the ELIS namespace second, and the individual ELIS subsystem or logical agent third.

ELIS adopts three governed Hermes runtime domains:

```text
Hermes
├── elis-core
├── elis-research
└── elis-github
```

Runtime domain and logical agent/profile identity must not be conflated. Canonical Git profiles remain flat under `profiles/hermes/<logical-profile>/`, while runtime-domain membership is represented separately as deployment/governance metadata.


Target semantics:

```text
/home/samurai/   human development, operator workspaces, staging, diagnostics, pilots
/opt/elis/       installed ELIS executable software
/etc/elis/       ELIS host configuration and policy
/var/lib/elis/   persistent internal service state, provenance, internal evidence
/var/log/elis/   persistent service logs where journald is insufficient
/run/elis/       ephemeral sockets, locks, credentials, tokens, runtime state
/srv/elis/       data intentionally served, published, or exported by ELIS
```

Technology-specific directories such as `/a2a`, `/hermes`, `/temporal`, or `/omnigent` should not be created at filesystem root.

---

## 3. Project Constraints

This is a controlled convergence project.

It does **not** authorize:

- mass filesystem moves;
- bulk renaming;
- recursive cleanup based only on naming;
- moving validated provenance merely for consistency;
- changing service identities without a separate security review;
- replacing functioning production components simply because their current path is non-canonical;
- modifying multiple critical runtimes in one change window;
- changing canonical Git content and live runtime content independently.

Every migration must be bounded, reversible where practical, validated independently, and completed before the next migration begins.

---

## 4. Infrastructure Classification

Every component or directory discovered during normalization must receive both:

### 4.1 Lifecycle classification

```text
CORE_PRODUCTION
PRODUCTION_SUPPORT
EXTERNAL_DEPENDENCY
DEVELOPMENT
PILOT
TRANSITIONAL
RETIRED
```

### 4.2 Filesystem disposition

```text
CANONICAL
ACCEPTABLE_LEGACY
DEV_ONLY
PILOT
MIGRATE_LATER
RETIRE
DELETE_AFTER_CLOSEOUT
```

No component should be moved until both classifications are explicit.

---

### 4.3 Architecture conformance status

Every production component, logical agent, adapter, worker, document, script, runtime, and filesystem location reviewed by this project must be mapped against the Taxonomy using:

```text
CURRENT_STATE=
REQUIRED_TARGET_STATE=
COMPLIANCE_STATUS=
TRANSITIONAL_STATE_ALLOWED=
COMPLIANCE_GAP=
ACTION=
TARGET_PHASE=
```

Allowed `COMPLIANCE_STATUS` values are:

- `COMPLIANT`
- `TEMPORARY_NONCOMPLIANT`
- `MIGRATE`
- `MERGE`
- `REPLACE`
- `DELETE`
- `BLOCKED`

`TEMPORARY_NONCOMPLIANT` is allowed only when:

- the current component is still required to keep production safe or available;
- the required final target is already known;
- a named phase owns the migration;
- the transitional state is not presented as the desired architecture.

No component may be declared compliant merely because its current design is locally reasonable or operational.

### 4.4 Simplification requirement

Normalization must reduce historical layering rather than merely relocate it.

For each simplification wave, record:

```text
ARTIFACT_COUNT_BEFORE=
ARTIFACT_COUNT_AFTER=

DUPLICATE_AUTHORITY_COUNT_BEFORE=
DUPLICATE_AUTHORITY_COUNT_AFTER=

LEGACY_MECHANISM_COUNT_BEFORE=
LEGACY_MECHANISM_COUNT_AFTER=

AGENT_SPECIFIC_INFRA_COUNT_BEFORE=
AGENT_SPECIFIC_INFRA_COUNT_AFTER=
```

Expected direction:

```text
ARTIFACT_COUNT_AFTER <= ARTIFACT_COUNT_BEFORE
DUPLICATE_AUTHORITY_COUNT_AFTER <= DUPLICATE_AUTHORITY_COUNT_BEFORE
LEGACY_MECHANISM_COUNT_AFTER <= LEGACY_MECHANISM_COUNT_BEFORE
AGENT_SPECIFIC_INFRA_COUNT_AFTER <= AGENT_SPECIFIC_INFRA_COUNT_BEFORE
```

A new shared component may increase the shared-infrastructure count only when it replaces multiple duplicated agent-specific mechanisms or implements a capability explicitly required by the Taxonomy.

## 5. Target ELIS Server Structure

The long-term production target is approximately:

```text
/
├── opt/
│   └── elis/
│       ├── hermes/
│       ├── temporal/
│       ├── a2a/
│       ├── litellm/
│       └── tools/
│
├── etc/
│   └── elis/
│       ├── hermes/
│       ├── temporal/
│       ├── a2a/
│       ├── litellm/
│       └── policies/
│
├── var/
│   ├── lib/
│   │   └── elis/
│   │       ├── hermes/
│   │       │   ├── elis-core/
│   │       │   │   ├── elis-advisor/
│   │       │   │   ├── elis-ideas/
│   │       │   │   ├── elis-pm/
│   │       │   │   └── elis-supervisor/
│   │       │   ├── elis-research/
│   │       │   │   ├── elis-research/
│   │       │   │   └── elis-slr-.../
│   │       │   └── elis-github/
│   │       │       └── elis-github/
│   │       ├── temporal/
│   │       ├── a2a/
│   │       ├── litellm/
│   │       ├── provenance/
│   │       ├── evidence/
│   │       ├── worktrees/
│   │       ├── reviews/
│   │       ├── handoffs/
│   │       └── github/
│   │           └── worktrees/
│   │
│   └── log/
│       └── elis/
│           ├── hermes/
│           ├── temporal/
│           ├── a2a/
│           └── litellm/
│
├── run/
│   └── elis/
│       ├── hermes/
│       ├── temporal/
│       ├── a2a/
│       └── litellm/
│
├── srv/
│   └── elis/
│       ├── public/
│       ├── exports/
│       └── evidence-library/
│
└── home/
    └── samurai/
        ├── src/
        ├── work/
        ├── pilots/
        └── archive/
```

This is a target architecture, not a command to create all directories immediately.

---

## 6. Canonical Git Structure

Git must represent canonical logical profile identity rather than Linux deployment paths or runtime-domain nesting.

ELIS operates three governed Hermes runtime domains:

```text
Hermes
├── elis-core
├── elis-research
└── elis-github
```

These domains describe **where and under what governance a profile runs**. They do not determine the canonical Git path of the profile.

### 6.1 Canonical Hermes profile paths

Use:

```text
profiles/hermes/<logical-profile>/...
```

Examples:

```text
profiles/hermes/elis-pm/
profiles/hermes/elis-advisor/
profiles/hermes/elis-ideas/
profiles/hermes/elis-supervisor/
profiles/hermes/elis-research/
profiles/hermes/elis-github/
profiles/hermes/elis-slr-.../
profiles/hermes/infra-.../
profiles/hermes/prog-.../
```

For `elis-github`:

```text
profiles/hermes/elis-github/SOUL.md
profiles/hermes/elis-github/memories/MEMORY.md
profiles/hermes/elis-github/skills/github/github/SKILL.md
```

### 6.2 Runtime-domain membership

Runtime-domain membership must be maintained separately.

Approved current mapping:

```text
elis-core
  elis-pm
  elis-advisor
  elis-ideas
  elis-supervisor
  infra-*
  prog-*

elis-research
  elis-research
  elis-slr-*

elis-github
  elis-github
```

A dedicated runtime/deployment manifest may later formalize this mapping.

The normalization project must not infer runtime-domain ownership solely from a profile's filesystem or Git path.

### 6.3 Separation-of-concerns rule

```text
Canonical Git profile path = logical profile identity
Runtime-domain mapping      = deployment/governance metadata
Linux filesystem path       = operational function
```

This separation is mandatory because it prevents profile renames or Git tree migrations when runtime placement changes.

## 7. Current-State Principles

The project should assume the current server contains a mixture of:

- production components;
- user-mode runtimes;
- dedicated service runtimes;
- development clones;
- migration candidates;
- diagnostics;
- pilots;
- legacy paths;
- historical evidence;
- retired infrastructure.

This mixture is expected after iterative ELIS development.

The normalization project must distinguish them instead of treating all filesystem content as equivalent.

Examples of important current distinctions include:

- production `elis-github` is isolated from the ordinary `samurai` Hermes runtime;
- A2A processes may represent adapters/endpoints for logical agents rather than independent logical agents;
- Temporal currently has development-style runtime characteristics but is intended to become core orchestration infrastructure;
- Omnigent remains a pilot;
- historical or migration-specific evidence has no automatic preservation privilege; retention, migration, export, or deletion is determined explicitly by current governance and lifecycle policy.

---

## 7.1 Architecture-by-contract diagnostic rule

Self-diagnostics and simplification inventories performed by `elis-advisor`, `elis-supervisor`, `elis-github`, `elis-pm`, research agents, workers, or external implementation models must not invent their own target architecture.

Required evaluation flow:

```text
OBSERVED_CURRENT_STATE
        ↓
ELIS_Production_Infrastructure_Taxonomy_v1.0
        ↓
REQUIRED_TARGET_STATE
        ↓
COMPLIANCE_GAP
        ↓
BOUNDED_TRANSFORMATION_ACTION
```

The diagnostic agent may challenge observed facts and recommend the safest path to compliance. It may not promote an incompatible current arrangement into a new architecture simply because migration would be inconvenient.

## 7.2 One-owner conformance rule

The transformation project must enforce the Taxonomy's canonical ownership mapping.

In particular:

- Worktree Manager owns worktree lifecycle and related filesystem permissions.
- Shared ELIS Preflight / Enforcement owns deterministic policy/preflight checks.
- Temporal owns durable orchestration.
- Hermes owns agent execution.
- A2A is transport/adaptation only when retained.
- LiteLLM owns model routing.
- Git owns canonical reviewed source.
- `SOUL.md`, `SKILL.md`, and `MEMORY.md` retain their distinct authority roles.

A migration that moves one concern from one duplicate implementation into another duplicate implementation is incomplete.

# 8. Phased Transformation Plan

## Phase 0 — Freeze the Taxonomy and Project Rules

### Objective

Establish the filesystem taxonomy and normalization method before moving anything.

### Actions

1. Treat `ELIS_Production_Infrastructure_Taxonomy_v1.0` as the working target contract.
2. Define the allowed lifecycle classifications.
3. Define the allowed filesystem dispositions.
4. Establish the rule that normalization is incremental.
5. Establish the rule that Git canonicalization precedes production-profile migration.
6. Establish that historical/provenance retention is explicit: no artifact is retained solely because it is historical, and no validated evidence is moved or deleted without the applicable PO/governance disposition.
7. Establish stop/return-to-PO gates for every production migration.
8. Establish that the Taxonomy and this Project are the only normative prose architecture/transformation authorities; component runbooks, manifests, scripts, and diagnostics are derived artifacts.

### Exit criteria

```text
TAXONOMY_ACCEPTED=YES
MASS_MIGRATION_AUTHORIZED=NO
INCREMENTAL_MIGRATION_REQUIRED=YES
```

---

## Phase 1 — Build the Authoritative Infrastructure Inventory

### Objective

Create one compact inventory of the actual ELIS production and support infrastructure.

### Inventory dimensions

For every discovered component record:

- component name;
- logical role;
- runtime;
- lifecycle classification;
- Unix user/group;
- systemd unit, if any;
- executable path;
- configuration path;
- state path;
- log path;
- runtime/ephemeral path;
- canonical Git source;
- active process;
- network/listening endpoints;
- dependency relationships;
- current filesystem disposition;
- target filesystem disposition.
- runtime-domain membership;
- canonical logical profile path;

### Required coverage

At minimum:

- Hermes;
- Temporal;
- A2A;
- LiteLLM;
- Git/GitHub;
- GitHub App/token refresh;
- Discord integration;
- Tailscale;
- Omnigent;
- Obsidian, if used locally;
- logging/observability;
- secrets/configuration;
- remaining Kanban infrastructure;
- ELIS Worktree Manager;
- current provenance/evidence roots;
- specialist SLR profiles;
- generic `infra-*` and `prog-*` profiles.

### Output

A machine-readable inventory and a human-readable summary.

Suggested artifacts:

```text
docs/infrastructure/ELIS_SERVER_INFRASTRUCTURE_INVENTORY.yaml
docs/infrastructure/ELIS_SERVER_INFRASTRUCTURE_INVENTORY.md
docs/infrastructure/ELIS_HERMES_RUNTIME_DOMAIN_MAP.yaml
```

`ELIS_HERMES_RUNTIME_DOMAIN_MAP.yaml` should map logical profiles to the approved runtime domains without changing their canonical Git paths.

### Exit criteria

Every production or production-support component has:

```text
CLASSIFICATION=KNOWN
CURRENT_PATHS=KNOWN
TARGET_PATHS=KNOWN
CANONICAL_SOURCE=KNOWN_OR_EXPLICITLY_UNKNOWN
```

No migrations occur in this phase.

---

## Phase 2 — Establish Git as the Canonical Source of Production Configuration

### Objective

Eliminate host-only canonical policy and profile definitions.

### Priority

Start with `elis-github`, because its production profile has already demonstrated the risk of host-only canonical configuration.

### Actions

1. Establish canonical runtime/profile paths under:

```text
profiles/hermes/<logical-profile>/
```

2. Ensure reviewed Git content is the source used for live deployment.
3. Establish hash-based canonical-to-live verification.
4. Define a deployment mechanism that copies reviewed bytes without semantic editing during deployment.
5. Record canonical Git commit/hash in deployment evidence.

### Required deployment invariant

```text
GIT_CANONICAL_BYTES == LIVE_DEPLOYED_BYTES
```

except for filesystem ownership, permissions, and other metadata.

### Exit criteria

At least one complete production profile proves the model:

```text
GIT_CANONICAL_SOURCE=YES
LIVE_HASH_MATCHES_GIT=YES
HOST_ONLY_CANONICAL_POLICY=NO
```

Then repeat for other production Hermes profiles.

---


## Phase 2A — Establish Task Worktree and Permission Boundaries

### Objective

Create the standard ELIS task execution boundary before broader runtime migration.

Target model:

```text
implementer source worktree
        ↓ FREEZE
validator read-only review
        ↓ PASS
validated read-only handoff
        ↓
elis-github publication worktree
        ↓
GitHub
```

### 2A.1 Establish dedicated production identities

Where operating-system permission boundaries matter, production agents must not share the `samurai` Unix identity.

Identify and plan dedicated identities for orchestrators, implementers, validators, and `elis-github`, including core, research, SLR, `infra-*`, and `prog-*` roles as required.

The migration to those identities may be phased, but the target permission model assumes distinct identities.

### 2A.2 Create canonical task worktree roots

Target:

```text
/var/lib/elis/worktrees/elis-core/<task-id>/repo/
/var/lib/elis/worktrees/elis-research/<task-id>/repo/
```

Do not create new mutable production worktrees under `/opt/elis`.

Existing `/opt/elis/agent-worktrees` content should be classified `MIGRATE_LATER` unless a separate retirement decision applies.

### 2A.3 Establish read-only reviewer visibility

For each task:

```text
implementer   RW
validator     R
orchestrator  R
elis-github   R
others        NONE
```

Read visibility may use domain-specific reader groups, but implementer write authority must remain task-specific.

### 2A.4 Implement Worktree Manager

Introduce the bounded production-support component:

```text
elis-worktree-manager
```

Allowed lifecycle operations:

```text
CREATE
FREEZE
REOPEN
HANDOFF
CLOSE
```

The manager owns privileged filesystem operations so agents do not require generic root-level permission-management capabilities.

### 2A.5 Implement freeze/reopen semantics

Required workflow:

```text
IMPLEMENTING
→ READY_FOR_VALIDATION
→ FREEZE
→ VALIDATING
→ PASS or FAIL
```

On `FREEZE`, the source worktree must become read-only for every agent.

On `FAIL`, explicit `REOPEN` may restore only the assigned implementer's write authority.

Every freeze must bind validation to repository, task ID, base commit, candidate commit, changed-file set, and content hashes or patch hash.

### 2A.6 Separate validator scratch/report state

Target:

```text
/var/lib/elis/reviews/<domain>/<task-id>/<validator>/
```

Validators must not generate cache, build, report, or coverage files inside implementation source trees.

### 2A.7 Standardize GitHub handoff

Target:

```text
/var/lib/elis/handoffs/github/<task-id>/
```

The handoff must be readable by `elis-github` and contain frozen reviewed artifacts or a patch plus manifest.

It must not require `elis-github` to traverse `/home/samurai`.

### 2A.8 Standardize `elis-github` publication worktrees

Target:

```text
/var/lib/elis/github/worktrees/<repository>/
```

These worktrees are writable only by the `elis-github` publication identity and are separate from implementation worktrees.

### 2A.9 Avoid shared writable Git metadata

Prefer task-local clones/repositories or another design that prevents independent identities from writing shared Git administrative metadata.

Do not use:

```text
safe.directory=*
```

as a cross-user workaround.

### 2A.10 Integrate with Temporal

Once Temporal is productionized, task lifecycle transitions should become durable workflow steps:

```text
CREATE_WORKTREE
IMPLEMENT
FREEZE
VALIDATE
REOPEN_IF_FAILED
CREATE_HANDOFF
PUBLISH
CLOSE
```

Temporal orchestrates these state transitions while Hermes agents perform bounded work.

### Required tests

```text
IMPLEMENTER_CAN_WRITE_ASSIGNED_WORKTREE=YES
IMPLEMENTER_CAN_WRITE_OTHER_WORKTREE=NO

VALIDATOR_CAN_READ_ASSIGNED_WORKTREE=YES
VALIDATOR_CAN_WRITE_SOURCE_WORKTREE=NO

ORCHESTRATOR_CAN_READ_WORKTREE=YES
ORCHESTRATOR_CAN_WRITE_WORKTREE=NO

ELIS_GITHUB_CAN_READ_VALIDATED_SOURCE=YES
ELIS_GITHUB_CAN_WRITE_TASK_WORKTREE=NO
ELIS_GITHUB_CAN_WRITE_PUBLICATION_WORKTREE=YES

FROZEN_WORKTREE_WRITER_COUNT=0
VALIDATED_HANDOFF_HASH_VERIFIED=YES
```

### Exit criteria

```text
TASK_WORKTREE_TOPOLOGY_DEFINED=YES
PER_TASK_WRITER_BOUNDARY_ENFORCED=YES
VALIDATOR_READ_ONLY_BOUNDARY_ENFORCED=YES
ORCHESTRATOR_READ_ONLY_BOUNDARY_ENFORCED=YES
ELIS_GITHUB_PUBLICATION_BOUNDARY_ENFORCED=YES
WORKTREE_MANAGER_AVAILABLE=YES
FREEZE_REOPEN_LIFECYCLE_TESTED=YES
```

## Phase 3 — Productionize Temporal

### Objective

Convert Temporal from a development-style runtime into explicitly managed production infrastructure.

### Target structure

```text
/opt/elis/temporal/       installed runtime/application
/etc/elis/temporal/       host configuration
/var/lib/elis/temporal/   persistent workflow state/database
/run/elis/temporal/       transient runtime state
```

Primary logging should use journald unless a separate persistent log path is justified.

### Actions

1. Identify the installed Temporal executable and version.
2. Identify the current development database/state.
3. Define the production persistence strategy.
4. Define a dedicated systemd service.
5. Define service identity and permissions.
6. Define startup/restart policy.
7. Define backup/restore procedure.
8. Define health checks.
9. Define rollback.
10. Migrate only after dry-run validation.

### Special requirement

The productionization must preserve Temporal workflow history and state where required.

### Exit criteria

```text
TEMPORAL_PRODUCTION_SERVICE=PASS
TEMPORAL_STATE_PATH_CANONICAL=YES
TEMPORAL_BACKUP_RESTORE_DEFINED=YES
TEMPORAL_HEALTH_CHECK=PASS
TEMPORAL_NO_PRODUCTION_DEPENDENCY_ON_HOME_SAMURAI=YES
```

---

## Phase 4 — Normalize Shared Production Infrastructure

### Objective

Move shared production-support services out of implicit user-owned locations where appropriate.

### 4.1 LiteLLM

Target:

```text
/opt/elis/litellm/
/etc/elis/litellm/
/var/lib/elis/litellm/
/run/elis/litellm/
```

Actions:

- confirm whether LiteLLM is required by production agents;
- freeze config;
- establish canonical Git source;
- migrate executable/config/state separately;
- use systemd;
- verify model-routing behavior after migration.

### 4.2 A2A

Target:

```text
/opt/elis/a2a/
/etc/elis/a2a/
/var/lib/elis/a2a/
/run/elis/a2a/
```

Actions:

- determine which A2A processes are required;
- formally classify them as adapters/endpoints where applicable;
- document their mapping to logical agents;
- establish service management;
- remove conceptual duplication between "A2A agent" and "Hermes agent."

### 4.3 Shared ELIS Preflight / Enforcement

**Classification:** shared production-support enforcement capability.

Target responsibility:

- repository/workspace binding;
- expected origin, branch, and HEAD;
- allowed changed-file scope;
- runtime identity checks;
- authorization state;
- canonical/live equality;
- permission invariants;
- CI/check-state validation where applicable;
- component-specific extension checks.

The shared Preflight / Enforcement capability must not absorb worktree lifecycle responsibilities. Those remain with Worktree Manager.

Existing component-specific preflight scripts may remain temporarily as `TEMPORARY_NONCOMPLIANT` implementations, but they must either:

- become thin component-specific extensions to the shared framework; or
- be retired once shared enforcement covers their unique checks.

### Exit criteria

```text
LITELLM_ROLE_EXPLICIT=YES
A2A_ROLE_EXPLICIT=YES
A2A_LOGICAL_AGENT_MAPPING_DOCUMENTED=YES
A2A_INDEPENDENT_AGENT_POLICY_COUNT=0
SHARED_PREFLIGHT_OWNER_EXPLICIT=YES
WORKTREE_MANAGER_PREFLIGHT_SCOPE_SEPARATED=YES
SHARED_SERVICES_MANAGED=YES
```

---

## Phase 5 — Normalize Hermes Production Runtime and Profiles

### Objective

Separate production Hermes execution from interactive/user-mode development Hermes.

### Current architectural distinction

A production deployment should have:

```text
installed code -> /opt/elis/hermes/
persistent state -> /var/lib/elis/hermes/<logical-agent>/
configuration -> /etc/elis/hermes/
```

Development/user-mode Hermes may remain under:

```text
/home/samurai/.hermes/
```

provided it is explicitly classified as development or transitional.

### Actions

1. Inventory every active Hermes profile.
2. Identify the actual production instance for each logical agent.
3. Identify duplicate/stale/development copies.
4. Canonicalize profile source in Git before moving runtime state.
5. Decide whether dedicated Unix identities are required per agent.
6. Migrate one logical agent at a time.
7. Define rollback and evidence retention/disposition explicitly for each migration; completed temporary artifacts must not become permanent architecture by default.
8. Do not move `elis-github` merely for naming consistency while its current isolated production boundary is healthy.

### Recommended migration order

Prefer lower-risk agents before security-sensitive `elis-github`.

Possible sequence:

```text
elis-ideas
elis-advisor
elis-pm
elis-research
elis-supervisor
elis-github (only if separately justified)
```

The actual order must be based on runtime dependency analysis.

### Exit criteria per agent

```text
CANONICAL_GIT_PROFILE=YES
RUNTIME_DOMAIN_ASSIGNED=YES
ROLE_BOUNDARY_EXPLICIT=YES
SOUL_AUTHORITY=YES
SKILL_PROCEDURE=YES
MEMORY_NON_AUTHORITATIVE=YES
SELF_MODIFICATION_ALLOWED=NO
SELF_DEPLOYMENT_ALLOWED=NO
SELF_APPROVAL_ALLOWED=NO
PRODUCTION_RUNTIME_EXPLICIT=YES
PRODUCTION_STATE_PATH_EXPLICIT=YES
DUPLICATE_AUTHORITY_COUNT=0
DUPLICATE_PROFILE_DISPOSITION=KNOWN
PRODUCTION_DEPENDENCY_ON_HOME_SAMURAI=0
HEALTH_CHECK=PASS
ROLLBACK_VALIDATED=YES
```

---

## Phase 6 — Rationalize Specialist Worker Profiles

### Objective

Make specialist agent naming and ownership understandable.

### Current profile families

Examples:

```text
elis-slr-<stage>-impl-a
elis-slr-<stage>-val-b

infra-impl-a
infra-impl-b
infra-val-a
infra-val-b

prog-impl-a
prog-impl-b
prog-val-a
prog-val-b
```

### Actions

1. Define the owner/orchestrator of each profile family.
2. Define whether each profile is production, support, development, or transitional.
3. Define canonical Git location.
4. Define whether the profile represents a long-lived agent identity or an execution worker.
5. Remove abandoned/superseded profiles only after confirming no active workflow references them.

### Exit criteria

No specialist profile exists without:

```text
OWNER=KNOWN
PURPOSE=KNOWN
LIFECYCLE=KNOWN
CANONICAL_SOURCE=KNOWN
```

---

## Phase 7 — Normalize Configuration, Secrets, Logs, and Runtime State

### Objective

Remove implicit configuration coupling and make operational data classes predictable.

### Configuration

Target:

```text
/etc/elis/<component>/
```

### Secrets

Secrets should:

- use restrictive ownership/modes;
- not be committed to Git;
- not be copied into operator workspaces;
- not be exposed through logs;
- have a documented rotation process.

### Logs

Prefer:

```text
journald
```

for systemd-managed services.

Use:

```text
/var/log/elis/<component>/
```

only where specialized persistent logs are justified.

### Ephemeral state

Target:

```text
/run/elis/<component>/
```

for:

- sockets;
- locks;
- short-lived tokens;
- PID/runtime markers;
- other reboot-ephemeral state.

### Exit criteria

```text
CONFIG_PATHS_CANONICAL=YES
SECRETS_POLICY_DEFINED=YES
LOGGING_POLICY_DEFINED=YES
EPHEMERAL_STATE_PATHS_CANONICAL=YES
```

---

## Phase 8 — Normalize Provenance and Evidence

### Objective

Use consistent paths and explicit lifecycle policy for internal provenance and evidence.

### Future internal provenance

Preferred:

```text
/var/lib/elis/provenance/<operation>/
```

### Future internal audit/evidence

Preferred:

```text
/var/lib/elis/evidence/
```

### Served/published evidence

Use:

```text
/srv/elis/evidence-library/
```

only when data is intentionally served, published, or exported.

### Historical and migration-specific evidence

Historical evidence has no automatic permanent-retention privilege.

For each evidence/provenance set, explicitly classify:

```text
KEEP
MIGRATE
EXPORT
DELETE
```

Retention should be driven by current governance, audit, legal, research, or operational requirements. Completed migration workspaces, rollback copies, and special-purpose evidence may be deleted when no current requirement justifies retention.

### Exit criteria

```text
NEW_PROVENANCE_STANDARD=ACTIVE
EVIDENCE_LIFECYCLE_EXPLICIT=YES
NO_UNCLASSIFIED_HISTORICAL_EVIDENCE=YES
SRV_USED_ONLY_FOR_SERVED_OR_PUBLISHED_DATA=YES
```

---

## Phase 9 — Clean and Structure `/home/samurai`

### Objective

Return the operator home directory to its appropriate role: development, staging, diagnostics, pilots, and archives.

### Target organization

```text
/home/samurai/
├── src/
├── work/
├── pilots/
└── archive/
```

Suggested semantics:

```text
src/       active Git working clones
work/      bounded engineering workspaces and diagnostics
pilots/    experimental systems such as Omnigent
archive/   retained operator material no longer active
```

### Important safety rule

Do not mass-move or delete current workspaces.

Before changing any workspace:

1. search scripts and documentation for path references;
2. identify whether the workspace is still active;
3. determine whether evidence must be preserved;
4. identify canonical Git replacement where applicable;
5. archive or retire only after dependency checks pass.

### Exit criteria

```text
PRODUCTION_RUNTIME_DEPENDENCY_ON_HOME_SAMURAI=0
ACTIVE_WORKSPACES_CLASSIFIED=YES
STALE_WORKSPACES_CLASSIFIED=YES
```

---

## Phase 10 — Retire Duplicate and Transitional Infrastructure

### Objective

Remove obsolete runtime copies and components after the canonical replacements are proven.

Potential targets include:

- duplicate Hermes profile copies;
- superseded SLR profiles;
- obsolete A2A components if Temporal supersedes them;
- Hermes Kanban orchestration remnants;
- retired broker artifacts;
- stale development daemons;
- unused migration launchers;
- superseded helper scripts.

### Required retirement rule

Every retirement must have:

```text
CANONICAL_REPLACEMENT=KNOWN
ACTIVE_DEPENDENCY_COUNT=0
EVIDENCE_RETENTION_DISPOSITION=DECIDED
ROLLBACK_OR_RECOVERY_DECISION=DOCUMENTED
```

### Exit criteria

No transitional component remains without an explicit disposition date or dependency reason.

---

## Phase 11 — Enforce the Taxonomy Automatically

### Objective

Prevent architecture drift after normalization.

### Recommended preflight assertions

```text
EXECUTABLE_LOCATION_OK
CONFIG_LOCATION_OK
STATE_LOCATION_OK
LOG_LOCATION_OK
RUNTIME_STATE_LOCATION_OK
SERVICE_IDENTITY_OK

CANONICAL_GIT_SOURCE_PRESENT
LIVE_PROFILE_MATCHES_CANONICAL_HASH
LIVE_CANONICAL_DRIFT_COUNT=0

DUPLICATE_AUTHORITY_COUNT=0
LEGACY_EXECUTION_PATH_COUNT=0
PRODUCTION_DEPENDENCY_ON_HOME_SAMURAI=0
MUTABLE_PRODUCTION_WORKTREE_UNDER_OPT_COUNT=0

A2A_INDEPENDENT_AGENT_POLICY_COUNT=0
A2A_INDEPENDENT_CREDENTIAL_OWNER_COUNT=0
A2A_INDEPENDENT_DURABLE_ORCHESTRATION_COUNT=0

AGENT_OWNED_DURABLE_ORCHESTRATION_COUNT=0
SHARED_PREFLIGHT_ENFORCEMENT_ACTIVE=YES
WORKTREE_MANAGER_SCOPE_COMPLIANT=YES

NO_UNCLASSIFIED_RUNTIME
NO_UNCLASSIFIED_PROFILE
FILESYSTEM_TAXONOMY_VIOLATION_COUNT=0
```

### Possible enforcement mechanisms

- CI checks;
- deployment preflight;
- host audit script;
- systemd unit validation;
- periodic infrastructure inventory;
- canonical-profile hash verification;
- configuration-policy tests.

### Exit criteria

The taxonomy is no longer merely documentation; violations become detectable before production deployment.

---

# 9. Standard Production Component Contract

Every production or production-support component should eventually have a machine-readable manifest.

The manifest is a derived enforcement representation of the Taxonomy, not an independent architecture authority. If it conflicts with the Taxonomy, the Taxonomy governs and the manifest must be corrected.

Example:

```yaml
component: temporal
classification: CORE_PRODUCTION

canonical_source:
  repository: elis-core/elis-core
  path: temporal/

runtime:
  installed_path: /opt/elis/temporal
  service_manager: systemd
  service_unit: elis-temporal.service
  identity: <service-user>

configuration:
  path: /etc/elis/temporal

persistent_state:
  path: /var/lib/elis/temporal

ephemeral_state:
  path: /run/elis/temporal

logging:
  primary: journald

provenance:
  path: /var/lib/elis/provenance

dependencies:
  - hermes
  - temporal-persistence

backup:
  required: true
  procedure: <reference>

health:
  check: <reference>
```

This contract should eventually cover:

- Hermes;
- Temporal;
- A2A;
- LiteLLM;
- GitHub integration;
- other services promoted to production.

---

# 10. Migration Gate for Every Production Change

Every migration should follow the same bounded sequence.

## PREPARE

- inventory current state;
- identify canonical source;
- record hashes;
- identify dependencies;
- define rollback;
- prepare candidate;
- validate candidate without mutation.

## REVIEW

- independent review;
- exact diff;
- scope verification;
- security/permission verification;
- PO authorization.

## EXECUTE

- fail closed on unexpected prestate;
- bounded mutation;
- no unrelated cleanup.

## VALIDATE

- service health;
- process identity;
- permissions;
- state integrity;
- canonical-to-live hash equality;
- dependency checks;
- no residual old runtime dependency.

## CLOSE

- apply the approved evidence-retention/disposition decision;
- delete temporary migration artifacts that no longer have a required function;
- update inventory;
- update canonical documentation;
- classify old path as retired/legacy;
- only then proceed to the next component.

---

# 11. Project Priority Order

The recommended order is:

```text
1.  Finish elis-github canonical Git representation
2.  Freeze Taxonomy v1.0 as the working infrastructure contract
3.  Build authoritative infrastructure inventory
4.  Establish task worktree + permission topology
5.  Introduce Worktree Manager and freeze/reopen lifecycle
6.  Standardize validated GitHub handoffs and elis-github publication worktrees
7.  Productionize Temporal
8.  Normalize LiteLLM
9.  Clarify and normalize A2A adapters
10. Canonicalize remaining Hermes profiles
11. Normalize production Hermes runtime/state
12. Normalize configuration, secrets, logs, and /run state
13. Normalize future provenance/evidence paths
14. Remove production dependencies from /home/samurai
15. Retire duplicate/transitional infrastructure
16. Add automated taxonomy enforcement
```

This sequence may be adjusted where dependency analysis shows a safer order.

---

# 12. Risk Management

Major risks include:

### Runtime outage

Mitigation:

- one component at a time;
- health checks before and after;
- explicit rollback.

### Canonical/live divergence

Mitigation:

- Git-first publication;
- exact hash verification;
- no live semantic edits after review.

### Permission regression

Mitigation:

- preserve owner/group/mode;
- validate Unix identity;
- negative permission tests.

### Hidden path dependency

Mitigation:

- read-only recursive reference search before migration;
- process inspection;
- systemd inspection;
- configuration inspection.


### Cross-agent write contamination

Mitigation:

- one assigned implementer writer per task;
- validator, orchestrator, and `elis-github` read-only source access;
- freeze before validation;
- explicit reopen after failed validation.

### Validation TOCTOU

Mitigation:

- freeze source before validator starts;
- bind validator result to commit/hash/manifest;
- no concurrent source writer during validation.

### Publication identity/path leakage

Mitigation:

- standard frozen handoff;
- `elis-github`-owned publication worktree;
- no publication directly from operator or implementer workspaces;
- no personal GitHub credential fallback.

### Loss of provenance

Mitigation:

- define retention requirements before destructive cleanup;
- retain/hash evidence only when current governance requires it;
- ensure deletions do not erase evidence that is still required.

### Premature cleanup

Mitigation:

- classification before deletion;
- `RETIRE` only after zero active dependency evidence.

---

# 13. Project Success Criteria

The filesystem normalization project is complete when:

1. every production component has an explicit lifecycle classification;
2. every production component has a canonical Git source;
3. installed software is predictably located;
4. configuration is predictably located;
5. persistent state is predictably located;
6. ephemeral runtime state is predictably located;
7. production services no longer depend unintentionally on `/home/samurai`;
8. logical agents and runtime implementations are clearly distinguished;
9. duplicate/transitional profiles have explicit dispositions;
10. internal provenance uses the approved `/var/lib/elis` convention;
11. `/srv/elis` is limited to served/published/exported material;
12. live deployed configuration can be verified against canonical Git content;
13. automated preflight detects taxonomy violations;
14. another experienced Linux developer can understand the ELIS production layout without reconstructing project history.
15. implementers can write only assigned task worktrees;
16. validators and orchestrators have read-only source access;
17. frozen validation states have zero source writers;
18. `elis-github` publishes only through validated handoffs and its own publication worktrees.
19. duplicate architectural authority is zero;
20. legacy execution paths are zero;
21. A2A adapters own transport only, with no independent agent policy or credential authority;
22. durable orchestration is owned by Temporal rather than agent-specific workflow logic;
23. shared preflight/enforcement is the canonical deterministic validation owner;
24. Worktree Manager owns only worktree lifecycle and associated filesystem permissions;
25. every production agent satisfies the standard logical-agent contract from the Taxonomy;
26. historical layering has been reduced rather than merely relocated.

---

# 14. Non-Goal

The project is not intended to create a perfectly uniform directory tree.

It is also not intended to preserve historical architecture generations merely because they existed. Transitional mechanisms should disappear after their required function has moved to the approved target owner.

Some existing paths may remain as `ACCEPTABLE_LEGACY` when moving them would add risk without operational benefit. Historical evidence is retained only when an explicit current requirement justifies retention.

The success criterion is **clear ownership, deterministic meaning, canonical source, and controlled lifecycle**, not cosmetic consistency.

---

# 15. Immediate Next Action

The next bounded action should be:

> Use the merged canonical `elis-github` V3 profile as the first architecture-conformance case: eliminate its legacy execution generations, deploy canonical Git bytes to the live profile, collapse duplicate authority, and classify every remaining component against the Taxonomy. In parallel, run read-only self-diagnostics for `elis-advisor` and `elis-supervisor` against the same contract.

The next transformations must close compliance gaps against the Taxonomy; they must not redefine the target architecture.


---

# 16. Normative Document Model

ELIS production infrastructure normalization uses two normative prose documents:

1. `ELIS_Production_Infrastructure_Taxonomy_v1.0`
   - authoritative target architecture;
   - ownership boundaries;
   - agent contract;
   - filesystem semantics;
   - infrastructure classifications.

2. `ELIS_Filesystem_Normalization_Gradual_Phased_Project_v1.0`
   - authoritative transformation/compliance plan;
   - phased migration;
   - conformance states;
   - validation gates;
   - simplification requirements.

Additional artifacts such as YAML manifests, CI checks, preflight scripts, runbooks, service definitions, agent diagnostics, and migration packets are **derived implementation or enforcement artifacts**.

They must not become independent architecture authorities.

Required precedence:

```text
Taxonomy
   ↓
Normalization Project
   ↓
derived machine-readable manifests / implementation plans
   ↓
preflight / CI / runtime enforcement
```

A component-specific diagnostic should therefore be able to receive only this instruction:

> Evaluate current state for compliance with the approved ELIS Production Infrastructure Taxonomy v1.0 and ELIS Filesystem Normalization Gradual Phased Project v1.0. Do not redesign the target architecture.

No repeated restatement of the full architecture contract should be necessary.
