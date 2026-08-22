# ELIS Production Infrastructure Taxonomy

**Version:** 1.0  
**Date:** 2026-08-22  
**Status:** Approved by Product Owner  
**Scope:** ELIS production infrastructure, supporting services, external dependencies, pilots, transitional components, and filesystem placement principles.
**Normative role:** This document is the authoritative ELIS production architecture contract. Agent diagnostics, implementation plans, runtime migrations, and supporting documents must conform to it and must not independently redesign the target architecture.

## 1. Purpose

This document defines the production infrastructure taxonomy for ELIS.

Its objectives are to:

- distinguish logical ELIS agents from the technologies used to execute, orchestrate, connect, and support them;
- establish a common classification for infrastructure components;
- clarify which technologies are core production dependencies, supporting services, external dependencies, development tools, pilots, transitional components, or retired components;
- provide a basis for normalizing the `elis-server` filesystem and runtime layout;
- prevent runtime technologies, agent identities, state, source code, operator workspaces, and historical evidence from being mixed without an explicit architectural rule.

A technology does not become a production subsystem merely because it currently runs on `elis-server`. Every component must have an explicit lifecycle and infrastructure classification.

**Architecture-by-contract rule**

> Current-state diagnostics discover facts. This Taxonomy determines the required target architecture. An agent, script, migration packet, or component-specific document may identify compliance gaps, but it must not create a competing target architecture.

Supporting documents may refine implementation details only within the boundaries defined here.


## 2. Architectural Dimensions

ELIS infrastructure should be described using four independent dimensions.

### 2.1 Logical agent identity

Examples:

- `elis-pm`
- `elis-advisor`
- `elis-github`
- `elis-ideas`
- `elis-research`
- `elis-supervisor`

Specialist worker profiles may use bounded role-oriented names, for example:

- `elis-slr-harvest-impl-a`
- `elis-slr-harvest-val-b`
- `infra-impl-a`
- `infra-val-a`
- `prog-impl-a`
- `prog-val-a`

The logical agent name must not imply a particular runtime implementation.

### 2.2 Runtime or infrastructure technology

Examples:

- Hermes
- Temporal
- A2A
- LiteLLM
- Discord
- Git/GitHub
- Tailscale
- Omnigent
- Obsidian

### 2.3 Filesystem role

Examples:

- source code;
- installed executable code;
- configuration;
- persistent mutable state;
- logs;
- ephemeral runtime state;
- operator workspace;
- provenance and evidence.

### 2.4 Lifecycle state

Every relevant component should be classified as one of:

- `CORE_PRODUCTION`
- `PRODUCTION_SUPPORT`
- `EXTERNAL_DEPENDENCY`
- `DEVELOPMENT`
- `PILOT`
- `TRANSITIONAL`
- `RETIRED`

## 2.5 Normative Authority, Ownership, and Agent Contract

This section defines cross-cutting rules that apply to every ELIS logical agent and infrastructure component.

### 2.5.1 Authority precedence

The production authority chain is:

```text
PO / active platform governance
        >
SOUL.md
        >
SKILL.md
        >
MEMORY.md
```

Required rules:

- `SOUL.md` defines the logical agent's role, authority, prohibitions, and stable governance boundary.
- `SKILL.md` defines agent-specific procedures within the authority granted by `SOUL.md`.
- `SKILL.md` must never broaden authority denied or omitted by `SOUL.md`.
- `MEMORY.md` is a non-authoritative context cache.
- `MEMORY.md` is not evidence and must not grant, broaden, or override authority.
- current evidence and canonical policy override remembered or historical context.
- technical capability does not imply authorization.

Required invariant:

```text
CAPABILITY_EQUALS_AUTHORIZATION=NO
SKILL_CAN_OVERRIDE_SOUL_PROHIBITION=NO
MEMORY_CAN_EXPAND_AUTHORITY=NO
```

### 2.5.2 One owner per concern

Each cross-cutting concern has one canonical owner:

| Concern | Canonical owner |
|---|---|
| Logical-agent authority | `SOUL.md` |
| Agent-specific procedure | `SKILL.md` |
| Non-authoritative operational context | `MEMORY.md` |
| Durable orchestration, sequencing, retries, and workflow state | Temporal |
| Agent/LLM execution | Hermes |
| Model routing | LiteLLM |
| Transport/protocol adaptation | A2A |
| Worktree lifecycle (`CREATE`, `FREEZE`, `REOPEN`, `HANDOFF`, `CLOSE`) | ELIS Worktree Manager |
| Filesystem authorization and privilege boundaries | Linux identities, groups, permissions, ACLs |
| Deterministic preflight and policy enforcement | Shared ELIS Preflight / Enforcement |
| GitHub production credential authority | GitHub App token runtime |
| Canonical source and reviewed configuration | Git |
| Installed software | `/opt/elis/` |
| Host configuration and policy | `/etc/elis/` |
| Persistent internal runtime state | `/var/lib/elis/` |
| Ephemeral runtime state | `/run/elis/` |
| Persistent logs where journald is insufficient | `/var/log/elis/` |

If two components independently own the same concern, the architecture is non-compliant until one ownership path is removed, merged, or explicitly subordinated.

### 2.5.3 ELIS Agent Simplicity Principle

Logical agents contain **role-specific intelligence only**. Cross-cutting concerns belong to shared ELIS infrastructure.

A new logical agent should normally require:

- a canonical profile;
- role-specific skills;
- runtime-domain assignment;
- model/runtime configuration;
- explicitly defined read/write privileges.

Adding a logical agent should **not** require a new:

- orchestration mechanism;
- credential architecture;
- worktree topology;
- preflight framework;
- transport architecture;
- policy hierarchy;
- logging/provenance subsystem;
- infrastructure stack.

Required rule:

> If adding the Nth logical agent requires infrastructure engineering comparable to introducing a new platform subsystem, the proposed architecture is non-compliant unless a unique requirement is explicitly approved.

Migration generations are temporary implementation history, not permanent architecture. A completed migration should reduce duplicate authority, legacy execution paths, and agent-specific infrastructure.

### 2.5.4 Logical agent, worker, adapter, and infrastructure component

ELIS uses the following deterministic classifications:

**Logical agent**

A persistent governed ELIS role with a stable logical identity and canonical authority profile.

Examples:

- `elis-pm`
- `elis-advisor`
- `elis-supervisor`
- `elis-github`
- `elis-research`

**Worker**

A bounded execution role used to perform a specific task or validation step. Workers should inherit shared platform behavior rather than own separate infrastructure architectures.

Examples:

- `infra-impl-a`
- `infra-val-b`
- `elis-slr-harvest-impl-a`

**Adapter**

A protocol/transport representation of a logical agent or service. An adapter must not independently own agent policy, credentials, durable workflow state, or business logic.

Example:

```text
elis.a2a.github = A2A adapter for the logical elis-github role, if retained
```

**Infrastructure component**

A shared platform capability such as Temporal, Hermes, LiteLLM, Worktree Manager, shared Preflight / Enforcement, Linux permission boundaries, or logging.

Required A2A invariant:

```text
A2A_INDEPENDENT_AGENT_POLICY_COUNT=0
A2A_INDEPENDENT_CREDENTIAL_OWNER_COUNT=0
A2A_INDEPENDENT_DURABLE_ORCHESTRATION_COUNT=0
```

### 2.5.5 Standard production logical-agent contract

Every production logical agent must converge on this common contract:

```text
CANONICAL_GIT_PROFILE=YES
RUNTIME_DOMAIN_ASSIGNED=YES
ROLE_BOUNDARY_EXPLICIT=YES

SOUL_AUTHORITY=YES
SKILL_PROCEDURE=YES
MEMORY_NON_AUTHORITATIVE=YES

SELF_DIAGNOSTIC_ALLOWED=YES
SELF_CRITIQUE_ALLOWED=YES

SELF_MODIFICATION_ALLOWED=NO
SELF_DEPLOYMENT_ALLOWED=NO
SELF_APPROVAL_ALLOWED=NO

DUPLICATE_AUTHORITY_COUNT=0
PRODUCTION_DEPENDENCY_ON_HOME_SAMURAI=0
```

A dedicated Unix identity is required where operating-system privilege separation materially enforces the role boundary.

An agent may inspect its own architecture and report compliance gaps. It must not treat self-diagnosis as authority to modify, deploy, or approve itself.

### 2.5.6 Shared ELIS Preflight / Enforcement

Deterministic production policy checks are a shared ELIS infrastructure concern.

The shared Preflight / Enforcement capability owns checks such as:

- repository binding;
- expected repository origin;
- expected branch and HEAD;
- allowed changed-file scope;
- runtime/service identity;
- authorization state;
- canonical-to-live equality;
- permission invariants;
- CI/check state where relevant;
- component-specific extension checks.

Component-specific scripts may exist temporarily, but they must converge on this shared ownership model instead of becoming independent policy authorities.

The Worktree Manager does **not** own GitHub policy, CI state, repository authorization, or general preflight semantics. Its scope is worktree lifecycle and associated filesystem permissions.

### 2.5.7 Machine-readable conformance representation

ELIS may maintain a machine-readable representation of this contract, for example:

```text
infrastructure/elis-production-contract.yaml
```

Such a manifest is a **derived enforcement artifact**, not an independent source of architectural authority.

Required relationship:

```text
Taxonomy -> normative architecture
machine-readable manifest -> derived representation
preflight/CI -> enforcement
```

If the derived manifest conflicts with this Taxonomy, this Taxonomy governs until the inconsistency is corrected.

## 3. ELIS Production Infrastructure Layers

### 3.1 Host Layer

**Components**

- Linux
- systemd
- Unix users and groups
- filesystem permissions and ownership
- networking
- Tailscale, where required for production access

**Classification**

- Linux: `CORE_PRODUCTION`
- systemd: `CORE_PRODUCTION`
- Unix identity and permission model: `CORE_PRODUCTION`
- Tailscale: `PRODUCTION_SUPPORT` or `EXTERNAL_DEPENDENCY`, depending on the deployed access architecture

**Responsibilities**

- process isolation;
- service lifecycle;
- boot activation;
- restart policy;
- privilege boundaries;
- filesystem security;
- network access controls.

### 3.2 Execution Layer

#### Hermes

**Classification:** `CORE_PRODUCTION`

Hermes is the current agent runtime for the principal ELIS logical agents.

ELIS adopts three governed Hermes runtime domains:

```text
Hermes
├── elis-core
├── elis-research
└── elis-github
```

The runtime domain and the logical profile are separate concepts. Canonical Git profiles remain keyed by logical profile identity, while runtime-domain membership is managed separately as deployment/governance metadata.


Current examples include:

- `elis-advisor`
- `elis-github`
- `elis-ideas`
- `elis-pm`
- `elis-research`
- `elis-supervisor`

**Architectural responsibility**

Hermes executes the reasoning and agent-level work assigned to a logical ELIS agent.

Hermes should not become the authoritative owner of cross-agent workflow durability when Temporal provides that function.

### 3.3 Orchestration Layer

#### Temporal

**Classification:** `CORE_PRODUCTION`

Temporal is the target deterministic orchestration substrate for ELIS.

**Responsibilities**

- durable workflows;
- sequencing;
- retries;
- failure handling;
- approval gates;
- concurrency control;
- workflow identity;
- idempotency;
- persistent execution history;
- recovery after process or host failures.

**Architectural rule**

> Temporal orchestrates. Hermes executes agent work.

#### Temporal persistence

**Classification:** `CORE_PRODUCTION`

Temporal persistence must be treated as a distinct operational responsibility even when initially implemented through Temporal's development database.

It requires explicit policies for durability, backup, restore, migration, data retention, and integrity.

### 3.4 Integration Layer

#### A2A

**Classification:** `PRODUCTION_SUPPORT`

A2A should be treated as an integration or adapter layer, not as a second set of logical ELIS agents.

Examples currently observed:

- `elis.a2a.advisor`
- `elis.a2a.github`
- `elis.a2a.pm`
- `elis.a2a.supervisor`

Where these processes provide protocol endpoints for the corresponding logical agents, governance and documentation should call them **A2A adapters/endpoints**, not independent agents.

An A2A adapter must not independently own agent policy, credentials, durable workflow state, or role-specific business logic. Those concerns remain with the logical agent or the appropriate shared ELIS infrastructure owner.

**Preferred conceptual model**

```text
Logical ELIS agent
        |
   Hermes runtime
        |
    A2A adapter
```

not:

```text
Hermes agent + separate A2A agent
```

If Temporal later supersedes part of the current A2A function, A2A may be reclassified as `TRANSITIONAL`.

#### Discord

**Classification:** `PRODUCTION_SUPPORT`

Discord is an operational communication and notification interface.

ELIS workflow correctness should not depend on Discord availability.

Discord should therefore be treated as a communication adapter rather than a core execution dependency.

### 3.5 AI and Model Access Layer

#### LiteLLM

**Classification:** `PRODUCTION_SUPPORT`

LiteLLM provides shared model-access infrastructure, including provider abstraction, model routing, fallback, rate management, cost controls, and endpoint normalization.

If ELIS production agents depend on LiteLLM for model access, it must be operated as a production service rather than as an implicit user utility.

#### Model providers

Examples:

- OpenRouter
- NVIDIA
- other approved inference providers

**Classification:** `EXTERNAL_DEPENDENCY`

These services provide model inference but are outside the ELIS host boundary.

### 3.6 Governance, Source, Identity, and Knowledge Layer

#### Git

**Classification:** `CORE_PRODUCTION`

Git provides versioning and change provenance for ELIS source code, policies, agent definitions, and governance artifacts.

#### GitHub

**Classification:** `CORE_PRODUCTION` for governance and canonical source management; externally hosted.

GitHub provides canonical repositories, pull-request review, controlled publication, versioned governance, code and policy provenance, collaboration, and auditability.

#### GitHub App and short-lived installation-token mechanism

**Classification:** `CORE_PRODUCTION`

The GitHub execution identity is a security-critical ELIS infrastructure component.

The approved production model uses:

- GitHub App identity;
- short-lived installation tokens;
- approved `gh` / `git` wrappers;
- explicit repository scope;
- no fallback to personal credentials.

The retired `gh-agentd` broker architecture must not be treated as a current fallback.

#### Obsidian

**Classification:** `DEVELOPMENT` or optional knowledge UI unless explicitly promoted.

Obsidian itself should not be the authoritative ELIS knowledge system.

Preferred architecture:

```text
Canonical Markdown / Git / ELIS evidence repositories
            |
        +---+---+
        |       |
      agents  Obsidian
              human UI
```

If agents consume a vault, the authoritative data should remain portable files and versioned evidence, not the Obsidian application.

## 4. Pilot and Transitional Components

### 4.1 Omnigent

**Current classification:** `PILOT`

Omnigent should remain outside the production architecture until ELIS explicitly adopts it as a production workspace, ACP coordination layer, or other durable platform component.

### 4.2 Hermes Kanban

**Current classification:** `TRANSITIONAL`

Hermes Kanban has served as an orchestration/task-management mechanism.

As Temporal assumes deterministic workflow orchestration, Kanban should no longer be treated as the authoritative execution state machine.

### 4.3 Duplicate or user-mode runtime representations

Profiles or runtime copies that duplicate a production logical agent but are not the live authoritative production instance must be classified explicitly as development, staging, backup, transitional, or retired.

They must not compete silently with the production canonical representation.

## 5. Approved Infrastructure Classification

### 5.1 Core production

- Linux host
- systemd
- Unix identity and permission model
- Hermes
- Temporal
- Temporal persistence
- Git
- GitHub
- GitHub App execution identity and short-lived token mechanism

### 5.2 Production support

- A2A
- LiteLLM
- Discord
- Tailscale/network access layer
- logging and observability
- health checks and runtime canaries
- ELIS Worktree Manager
- Shared ELIS Preflight / Enforcement
- configuration and secrets management

### 5.3 External dependencies

- OpenRouter
- NVIDIA and other approved model providers
- GitHub as an externally hosted platform
- other externally hosted services formally adopted by ELIS

### 5.4 Development / optional tooling

- Obsidian, unless promoted to a formally required knowledge interface
- local development clones
- operator diagnostics
- temporary candidate workspaces

### 5.5 Pilot

- Omnigent

### 5.6 Transitional

- Hermes Kanban as orchestration
- duplicate runtime/profile representations awaiting reconciliation
- legacy A2A components if Temporal supersedes their role
- other runtime components explicitly scheduled for migration or retirement

### 5.7 Retired

Examples include:

- `gh-agentd`
- `gh-agent-client`
- legacy `gh-agent` broker path
- other components formally decommissioned and removed according to their approved retention/disposition policy

## 6. Filesystem Contract

The production filesystem should be organized by **filesystem responsibility**, not by technology name at `/`.

### 6.1 `/home/samurai/`

**Purpose:** human/operator-owned development and temporary work.

Appropriate content:

- Git working clones;
- Claude CLI workspaces;
- migration candidates;
- experiments;
- diagnostic workspaces;
- pilots;
- staging material.

Production service state should progressively move out of the human home directory when a component becomes stable production infrastructure.

### 6.2 `/opt/elis/`

**Purpose:** installed ELIS executable software.

Target examples:

```text
/opt/elis/hermes/
/opt/elis/a2a/
/opt/elis/temporal/
/opt/elis/litellm/
/opt/elis/tools/
```

Do not store mutable runtime databases, tokens, logs, or operator workspaces here.

### 6.3 `/etc/elis/`

**Purpose:** host-level ELIS configuration and policy.

Target examples:

```text
/etc/elis/hermes/
/etc/elis/a2a/
/etc/elis/temporal/
/etc/elis/litellm/
/etc/elis/policies/
```

Secrets require appropriate restrictive ownership and modes.

### 6.4 `/var/lib/elis/`

**Purpose:** persistent internal ELIS service state and durable internal operational data.

Target examples:

```text
/var/lib/elis/hermes/elis-core/<logical-agent>/
/var/lib/elis/hermes/elis-research/<logical-agent>/
/var/lib/elis/hermes/elis-github/<logical-agent>/
/var/lib/elis/temporal/
/var/lib/elis/a2a/
/var/lib/elis/litellm/
/var/lib/elis/provenance/
/var/lib/elis/evidence/
/var/lib/elis/worktrees/
/var/lib/elis/reviews/
/var/lib/elis/handoffs/
/var/lib/elis/github/worktrees/
```

This is the preferred location for internal ELIS data that must survive service restarts or host reboots but is not itself intended to be directly served or published.

Appropriate content includes:

- persistent service state;
- workflow/datastore state;
- internal execution provenance;
- internal validation and audit evidence;
- decommission evidence;
- migration evidence;
- durable service-owned metadata.

The existing isolated `/var/lib/elis-github` deployment remains acceptable legacy/canonical production state until a separately governed migration is justified.

For future decommission operations, prefer:

```text
/var/lib/elis/provenance/<operation>/
```

rather than creating new top-level `/srv/<operation>` roots.

### 6.5 `/var/log/elis/`

**Purpose:** persistent ELIS service logs where journald alone is insufficient.

Target examples:

```text
/var/log/elis/hermes/elis-github/
/var/log/elis/temporal/
/var/log/elis/a2a/
```

systemd journal should remain the primary service log where appropriate.

### 6.6 `/run/elis/`

**Purpose:** ephemeral runtime state.

Examples:

- sockets;
- PID/runtime markers;
- locks;
- short-lived tokens;
- temporary credentials.

Nothing under `/run/elis` should be required to survive reboot.

### 6.7 `/srv/elis/`

**Purpose:** ELIS data intentionally served, published, or exported by a service.

Target examples:

```text
/srv/elis/public/
/srv/elis/exports/
/srv/elis/evidence-library/
```

Use `/srv/elis` only when the data is intentionally exposed to users, applications, APIs, websites, or other consumers as service content.

Examples include:

- public ELIS datasets;
- downloadable exports;
- published evidence libraries;
- web-served research material;
- other data whose operational purpose is to be served.

Internal provenance, audit evidence, decommission evidence, and mutable service state belong under `/var/lib/elis`, not `/srv/elis`.

The semantic distinction is:

```text
/var/lib/elis = ELIS owns and internally maintains it
/srv/elis     = ELIS serves or publishes it
```

### 6.8 Historical provenance and evidence lifecycle

Historical or migration-specific provenance has no automatic permanent-retention status.

For every such evidence set, current governance must explicitly decide one disposition:

```text
KEEP
MIGRATE
EXPORT
DELETE
```

If retained internally, future placement should follow the `/var/lib/elis/...` convention unless an explicitly accepted legacy location remains safer for a bounded period.

Only material intentionally served or published should use `/srv/elis/...`.

Completed migration workspaces, rollback copies, and special-purpose decommission evidence should be deleted when no current audit, legal, research, operational, or governance requirement justifies retention.

### 6.9 Do not create technology directories at filesystem root

The following root-level directories should not be introduced:

```text
/a2a
/hermes
/temporal
/omnigent
```

These names describe technologies or subsystems, not filesystem responsibilities.

Use the appropriate functional locations beneath `/opt/elis`, `/etc/elis`, `/var/lib/elis`, `/var/log/elis`, `/run/elis`, or `/srv/elis`.

### 6.10 ELIS filesystem semantics summary

| Path | ELIS meaning |
|---|---|
| `/home/samurai/` | human development, operator workspaces, staging, diagnostics, and pilots |
| `/opt/elis/` | installed ELIS executable software |
| `/etc/elis/` | ELIS host configuration and policy |
| `/var/lib/elis/` | persistent internal state, provenance, and internal evidence |
| `/var/log/elis/` | persistent service logs where journald is insufficient |
| `/run/elis/` | ephemeral sockets, locks, tokens, and runtime state |
| `/srv/elis/` | data intentionally served, published, or exported by ELIS |

This convention follows standard Linux filesystem semantics first, the ELIS application namespace second, and individual ELIS technologies or logical agents third.

## 7. Canonical Git Structure

Git should represent **logical architecture and canonical profile identity**, not reproduce Linux deployment paths or runtime-domain placement.

ELIS operates three governed Hermes runtime domains:

```text
Hermes
├── elis-core
├── elis-research
└── elis-github
```

These runtime domains are a **deployment and governance topology**. They are deliberately separate from the canonical Git path of a logical Hermes profile.

### 7.1 Canonical Hermes profile convention

Canonical Hermes profiles use the flat logical-profile convention:

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
profiles/hermes/elis-slr-harvest-impl-a/
profiles/hermes/infra-impl-a/
profiles/hermes/prog-val-b/
```

This convention matches the existing repository precedent and keeps a logical profile's canonical identity stable even if its runtime-domain placement changes later.

For the production Hermes `elis-github` authority profile, the approved canonical paths are:

```text
profiles/hermes/elis-github/SOUL.md
profiles/hermes/elis-github/memories/MEMORY.md
profiles/hermes/elis-github/skills/github/github/SKILL.md
```

### 7.2 Runtime-domain membership is separate metadata

Runtime-domain membership must be represented separately from profile path structure.

Current approved ownership model:

```text
elis-core
├── elis-pm
├── elis-advisor
├── elis-ideas
├── elis-supervisor
├── infra-*
└── prog-*

elis-research
├── elis-research
└── elis-slr-*

elis-github
└── elis-github
```

A future deployment/runtime-domain manifest may encode this mapping, but the profile path itself must not be used as the runtime-domain assignment mechanism.

This separation provides:

- stable canonical profile identity;
- independent runtime topology;
- easier reassignment of profiles between runtime domains;
- fewer repository path migrations;
- clearer separation between source governance and deployment governance.

### 7.3 Other runtime representations

Other runtimes may use their own explicit namespaces, for example:

```text
profiles/a2a/<logical-role-or-adapter>/
profiles/<other-runtime>/<logical-role>/
```

Where A2A processes are adapters for Hermes logical agents, documentation should describe them as adapters/endpoints rather than competing canonical agent definitions.


## 7.4 Task Worktree and Privilege Topology

ELIS production task execution must use a first-class worktree and handoff model rather than ad-hoc cross-user access to operator-owned directories.

### 7.4.1 Core principle

> **The assigned implementer has exclusive write authority over the task source worktree; validator, orchestrator, and `elis-github` have read-only visibility; publication occurs from a frozen handoff into an `elis-github`-owned publication worktree.**

This separates implementation, validation, orchestration, and publication privileges.

### 7.4.2 Target topology

Preferred internal paths:

```text
/var/lib/elis/
├── worktrees/
│   ├── elis-core/<task-id>/repo/
│   └── elis-research/<task-id>/repo/
├── reviews/
│   ├── elis-core/<task-id>/<validator>/
│   └── elis-research/<task-id>/<validator>/
├── handoffs/
│   └── github/<task-id>/
├── github/
│   └── worktrees/<repository>/
└── provenance/
    └── tasks/<task-id>/
```

Mutable task worktrees should not live under `/opt/elis`, because `/opt/elis` is reserved for installed software.

### 7.4.3 Production Unix identities

Linux permissions can only enforce separation when actors have distinct Unix identities.

Where privilege boundaries matter, production identities should be distinct, including as applicable:

```text
elis-pm
elis-advisor
elis-research
elis-supervisor
elis-github
infra-impl-*
infra-val-*
prog-impl-*
prog-val-*
elis-slr-...-impl-*
elis-slr-...-val-*
```

Running multiple logically independent production agents as `samurai` prevents the operating system from enforcing implementer/validator/orchestrator separation.

### 7.4.4 Task permission model

For an assigned task worktree:

```text
implementer   RW
validator     R
orchestrator  R
elis-github   R
others        NONE
```

The implementer's write authority must be per-task, not granted through a broad shared writers group.

Domain read groups may be used for read-only access, for example:

```text
elis-core-worktree-readers
elis-research-worktree-readers
```

`elis-github` must not receive write permission on implementation worktrees.

### 7.4.5 Worktree lifecycle

Normal lifecycle:

```text
IMPLEMENTING
    ↓
READY_FOR_VALIDATION
    ↓
FREEZE
    ↓
VALIDATING
    ↓
PASS → VALIDATED_HANDOFF
FAIL → REOPEN → IMPLEMENTING
```

During `IMPLEMENTING`, only the assigned implementer has write access.

During `FROZEN` / `VALIDATING`, the source has no writer. A failed validation may explicitly reopen the task and restore write permission only to the assigned implementer.

### 7.4.6 Validator isolation

Validators must not write into the implementation source tree.

Validator-generated caches, reports, coverage, build output, and other scratch state must use a separate writable location such as:

```text
/var/lib/elis/reviews/<domain>/<task-id>/<validator>/
```

### 7.4.7 Task-local Git metadata

Avoid writable shared Git administrative metadata across unrelated Unix identities.

Preferred model:

```text
read-only repository source/mirror
        ↓
task-local clone/repository
        ↓
implementer-owned task worktree
```

Do not solve cross-user Git ownership problems with global `safe.directory=*`.

### 7.4.8 ELIS Worktree Manager

ELIS should provide a bounded `elis-worktree-manager` production-support component.

Its allowed lifecycle responsibilities are:

```text
CREATE
FREEZE
REOPEN
HANDOFF
CLOSE
```

Agents should not require unrestricted `chown`, `chmod`, `setfacl`, `git worktree add`, or recursive deletion privileges.

The Worktree Manager is not the owner of generic policy/preflight enforcement. Repository authorization, expected origin/HEAD, CI state, allowed changed-file scope, and other deterministic policy checks belong to Shared ELIS Preflight / Enforcement.

The manager may initially be a root-owned helper or tightly scoped Temporal Activity rather than a network daemon.

### 7.4.9 Validated GitHub handoff

After validation, publication must use a frozen read-only handoff rather than a mutable implementation workspace.

Preferred path:

```text
/var/lib/elis/handoffs/github/<task-id>/
```

A handoff should bind publication to reviewed bytes and include sufficient provenance, for example:

```text
MANIFEST.yaml
PATCH.diff
VALIDATION.json
```

Representative manifest fields:

```yaml
task: t_example
repository: elis-core/elis-core
base_commit: <sha>
candidate_commit: <sha>
implementer: <identity>
validator: <identity>
validation: PASS
changed_files:
  - <path>
patch_sha256: <sha256>
```

### 7.4.10 `elis-github` publication boundary

`elis-github` must publish from its own writable repository/worktree, for example:

```text
/var/lib/elis/github/worktrees/<repository>/
```

Publication flow:

```text
validated source
      ↓
frozen handoff
      ↓
elis-github READ
      ↓
elis-github publication worktree RW
      ↓
GitHub
```

`elis-github` does not publish directly from an implementer-owned worktree.

### 7.4.11 Required permission invariants

The target implementation should make these assertions machine-testable:

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

SAMURAI_CREDENTIAL_FALLBACK_REQUIRED=NO
PERSONAL_GITHUB_CREDENTIAL_REQUIRED=NO
```

## 8. Production Promotion Rule

Before a component is classified as production infrastructure, ELIS should explicitly establish:

1. purpose;
2. lifecycle classification;
3. canonical source;
4. runtime owner;
5. installed code location;
6. configuration location;
7. persistent state location;
8. logs and observability;
9. ephemeral runtime state;
10. backup and recovery policy;
11. security boundary;
12. decommission procedure.

## 9. Migration Principle

The approved taxonomy does **not** authorize a mass filesystem reorganization.

Migration should proceed incrementally.

Each existing component should be classified as:

```text
CANONICAL
ACCEPTABLE_LEGACY
DEV_ONLY
PILOT
MIGRATE_LATER
RETIRE
DELETE_AFTER_CLOSEOUT
```

Cleanup should be aligned with ongoing Temporal and runtime modernization work.

The priority is architectural clarity and deterministic ownership, not cosmetic directory uniformity.

## 10. Core ELIS Infrastructure Principle

> **One logical agent identity, explicit runtime implementations, one canonical source in Git, and filesystem locations determined by operational function rather than by whichever project or migration created them.**

This principle should guide future ELIS server cleanup, Temporal migration, runtime deployment, agent-profile canonicalization, and infrastructure governance.


## 11. Architecture Conformance Rule

All agent self-diagnostics, simplification inventories, migration plans, and component-specific reviews must report current state **against this Taxonomy**.

They may recommend how to close a gap, but they must not redefine the required target architecture.

Required diagnostic shape:

```text
CURRENT_STATE=
REQUIRED_TARGET_STATE=
COMPLIANCE_STATUS=
COMPLIANCE_GAP=
TRANSITIONAL_STATE_ALLOWED=
FINAL_DISPOSITION=
```

The companion `ELIS_Filesystem_Normalization_Gradual_Phased_Project_v1.0` defines how non-compliant current state is transformed into this target.

Together, these two documents are sufficient as the normative prose architecture and transformation contract. Additional machine-readable manifests, scripts, tests, and runbooks are derived implementation/enforcement artifacts and must not become competing architecture authorities.
