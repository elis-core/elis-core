# ELIS GitHub Agent Operating Model

**Status:** Canonical — v1.1
**Date:** 2026-05-06
**Owner:** Carlos Rocha, Product Owner
**Applies to:** All ELIS agents with GitHub operations capability

## 1. Purpose
This document defines the GitHub Write Boundary Model for ELIS: the operating model that governs which roles may perform which GitHub write operations, under what gates, and with what approval. It supersedes ad-hoc permission patterns and codifies the boundary explicitly for every agent role.

### 1.2 Deterministic Enforcement Reference

The 14 skills and rules in `docs/ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md`
constitute the **deterministic enforcement layer** for this operating model.
Each rule in the skill pack maps to specific failure classes from the registry in
`docs/ops/github-agent/GITHUB_AGENT_RULES.md` and provides executable check
procedures, expected outputs, and failure responses.

Where this operating model defines the *what* and *why* of GitHub write boundaries,
the skill pack defines the *how* — the precise sequence of preflight checks,
verification steps, and output evidence required for each operation.

### 1.3 PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED — Formal Finding

**Status:** Open — Finding recorded 2026-06-04
**Source:** PE-OPS-GITHUB-SKILLS-01
**Target PE for remediation:** PE-OPS-GITHUB-PERMISSIONS-01

**Read-only audit:** A read-only audit of PM GitHub-capable paths was conducted
as part of PE-OPS-GITHUB-SKILLS-01. The audit checked for the existence and type
of GitHub write capabilities available to the PM role:

| Capability Path | Availability | Notes |
|----------------|-------------|-------|
| `gh` CLI auth status | Present | `gh auth status` confirms a configured GitHub identity (identity not disclosed per §4.4b) |
| `git push` over SSH | Present (via SSH agent) | SSH key at `~/.ssh/` allows push to `origin` |
| `git push` over HTTPS | Present (via credential helper) | Git credential helper caches credentials |
| `bin/gh-agent` | Executable but PM-prohibited | PM must not execute per operating model §4.4a |
| GitHub PAT or token file | Present (file path known) | Path: known to PM infra; content not inspected per SECRET_OUTPUT_RISK rule |

**Principle of audit:** This audit collected metadata only — file existence, command
availability, permission class. No credential content, token values, file contents,
or secret hashes were read or recorded. All evidence is limited to paths, command
availability status, and permission class identifiers.

**Target state:** PM should not retain standing GitHub write/merge capability except
a documented, PO-approved break-glass path. Target state requirements:
- PM `gh` auth is limited to read-only scope, or removed entirely
- PM has no `git push` capability to the ELIS remote (via credential removal or
  remote URL restriction to `--no-push`)
- Break-glass path is documented, approved by PO, and logged when used
  (including PO approval reference, exact command, SHA(s), rationale, timestamp,
  and post-operation boundary reset confirmation)

**Action taken in this PE:** Finding recorded in this section. Actual credential
restriction or removal is **out of scope** and deferred to
`PE-OPS-GITHUB-PERMISSIONS-01` by explicit plan instruction.

### 1.1 ELIS GitHub Identity / Actor Terminology

The following table defines the canonical ELIS GitHub identity layer — the set of identities,
actors, and credentials governed by this operating model:

| Identity | Type | Purpose | Governing Role |
|----------|------|---------|----------------|
| `elis-github` | OS user (service account) | Owns `bin/gh-agent`, credential files under `/opt/elis/secrets/`, and the canonical GitHub CLI context on elis-server | GitHub Agent, PM (routing only) |
| `elis-git-bot <elis-git-bot@electoralintegrity.org>` | Git commit author | Author name/email for all ELIS bot-generated commits pushed to GitHub | GitHub Agent (via `bin/gh-agent`) |
| `app/elis-github` | GitHub API / PR actor | Actor identity recorded in GitHub API events for PR creation, review, comment, merge, and label operations | GitHub Agent (via `bin/gh-agent`) |
| `elis-git-bot` | GitHub.com bot account | The GitHub user account associated with the bot identity; used for web UI login and manual fallback when automation is unavailable | PO / Carlos (emergency fallback only) |

**Security context:** The OS user `elis-github`, Git commit author `elis-git-bot`, GitHub API actor
`app/elis-github`, and GitHub.com bot account `elis-git-bot` are distinct bindings of the same
ELIS GitHub production identity. They must not be treated as separate actors with independent
authority boundaries. All GitHub write operations — regardless of binding — are governed by
the permission matrix in §5 and the launcher rule in §4.4a.

Cross-reference worked-example identity invocation: `docs/governance/ELIS_Worked_Example_GitHub_Identity_v1.md` *(not yet created — future PE scope)*

## 2. Scope
In scope:
- Role-based permission boundaries for GitHub operations
- allowed and forbidden GitHub operations per role
- PR, check, label, comment, review, and merge gates
- identity verification rules
- evidence packet requirements
- manual fallback path when automation fails
- relationship to the fixed agent workspace model

Out of scope:
- OpenClaw runtime/config changes
- ELIS code implementation
- merge authority without Carlos/PO approval
- unrelated platform recovery procedures

## 3. Core Principle: No Default GitHub Write Access
No agent role has default GitHub write access. Every GitHub write operation requires:
1. The action is within the role's authorised boundary (see §5)
2. The agent's fixed workspace identity is verified
3. The PE is active and the branch is current
4. PM or PO has authorised the specific operation

## 4. Role Model
### 4.1 Implementer
Produces branch work and implementation artefacts in the fixed implementer workspace. Local git operations only (commit). No default remote write access.

**Workspace:** `/opt/elis/agent-worktrees/<role>-<slot>` (e.g. `infra-impl-b`)

### 4.2 Validator
Performs independent review. Local git operations only (commit REVIEW file, adversarial tests). PR comments and formal GitHub reviews when explicitly authorised by PM.

**Workspace:** `/opt/elis/agent-worktrees/<role>-<slot>` (e.g. `infra-val-a`)

### 4.3 PM
Owns PE coordination, authorisation checkpoints, and fallback escalation. PM must **not** write to GitHub directly. All GitHub write operations (push, PR, labels, comments) must be executed by the GitHub Agent after explicit PM approval. PM coordinates and approves but does not operate GitHub write tools.

### 4.4 GitHub Agent (Dedicated Bot)
A permanent ELIS role with PE-scoped activation for write-capable GitHub operations: push, PR lifecycle, PR merge (when PO-approved), labels, comments, review requests, check reporting. Does not independently approve scope, validation, or merge — all merge operations require explicit PO approval before execution.

**PR merge routing:** PM receives PO merge approval, then routes the merge request to ELIS GitHub. ELIS GitHub executes the merge using its authorised credential boundary (`app/elis-github` identity). PM must not execute GitHub Agent binaries locally or access GitHub Agent credential files. Supervisor is the escalation path for errors only.

### 4.4a Mandatory Launcher Rule

All GitHub CLI operations that create, update, review, or merge PRs **must** use the
`bin/gh-agent` script. Direct `gh` invocation for mutating operations is prohibited.

**Rationale:** `bin/gh-agent` enforces the correct identity (`app/elis-github`), credential
source (`/opt/elis/secrets/github-agent.env`), fixed workspace path, and required gate checks
before executing any write-capable GitHub operation. Bypassing this wrapper risks identity
mismatch, credential leakage, or ungoverned write operations.

**Scope of mandatory use:**
- PR creation
- PR update (title, body, labels, reviewers, milestone)
- PR review submission (approve, comment, request changes)
- PR merge
- PR comment posting
- Push to remote

**Read-only exceptions:** Direct `gh` is permitted for read-only operations explicitly
documented in this file (see §4.4b).

### 4.4b Raw `gh` Policy

Direct `gh` invocation is permitted **only** for read-only, non-mutating operations explicitly
documented in this file. Permitted read-only `gh` operations include:
- `gh pr list` (list open PRs)
- `gh pr view <number>` (view PR details)
- `gh run list` (list workflow runs)
- `gh run view <run-id>` (view run details)
- `gh api GET ...` (read-only API calls)
- `gh auth status` (verify current auth context — must resolve to identity governed by this model)

**TEMPORARY_HUMAN_GITHUB_AUTH_RISK / GITHUB_ACTOR_MISMATCH classification:**

Any `gh` invocation — read or write — whose resolved GitHub user identity is `rochasamurai`
must be classified as one of:
- `TEMPORARY_HUMAN_GITHUB_AUTH_RISK` — when the context is a known migration, setup, or
  emergency fallback under explicit PO authorisation
- `GITHUB_ACTOR_MISMATCH` — when the resolved identity does not match the governed ELIS GitHub
  identity documented in §1.1 and no explicit PO authorisation exists

PM must not route, approve, or silently allow any operation where the resolved `gh` identity
is `rochasamurai` without first confirming the classification and obtaining PO approval if the
context is `GITHUB_ACTOR_MISMATCH`.

### 4.4c A2A Request/Report Flow Stub (github-agent)

**Status:** Mailbox creation deferred to Gate 2.

The GitHub Agent will participate in A2A messaging for request/report flows once its A2A
mailbox is created and the communication matrix is updated. Until then, all GitHub Agent
communication uses the Discord-based routing path defined in the PM orchestration rules.

**Planned A2A message types (post-mailbox creation):**
- `GITHUB_OPERATION_REQUEST_V1` — PM requests a GitHub write operation
- `GITHUB_OPERATION_REPORT_V1` — GitHub Agent reports operation result
- `GITHUB_STATUS_REQUEST_V1` — PM requests GitHub Agent status
- `GITHUB_STATUS_REPORT_V1` — GitHub Agent reports operational status

### 4.4d Secret Boundary — `/opt/elis/secrets/github-agent.env`

**Purpose:** The file `/opt/elis/secrets/github-agent.env` contains the GitHub token and
credential context used by `bin/gh-agent` for all governed GitHub write operations.

**File existence:** The file must exist at `/opt/elis/secrets/github-agent.env` for the
github-agent role to function. If the file is absent, `bin/gh-agent` must fail closed — no
GitHub write operation may proceed.

**Permissions:** The file must be readable only by the `elis-github` OS user. Minimum
permissions: `600` (owner read/write). The file must not be world-readable, group-readable,
or readable by any OpenClaw/Hermes agent runtime process.

**Access prohibitions:**
- No OpenClaw agent (implementer, validator, PM, supervisor, advisor) may read this file
- No Hermes agent may read this file
- No CI/CD pipeline step that runs as a non-"elis-github" user may read this file
- PM must not reference, read, or access credential file contents — PM routes merge requests,
  it does not handle credentials
- Any attempt to `cat`, `source`, or otherwise inspect file contents from an ungoverned
  context is a credential boundary violation

**Note to implementers:** This section documents file existence and permissions requirements
only. File contents have not been inspected. No credential mutation has occurred.

### 4.5 Carlos / PO
Final approval authority for merge, scope exceptions, and any escalation that changes repository state.

### 4.6 Supervisor
- Monitors PE workflow integrity and role compliance
- Reads repo state (branches, PRs, CI status, artefact existence)
- Detects role boundary violations (e.g., implementer pushing, PM writing to GitHub)
- Detects missing artefacts (HANDOFF, REVIEW, Status Packet)
- Reports findings to PM
- Must not write to GitHub (no commits, push, PR, label, or comment)
- Must not dispatch agents
- Must not perform implementation or validation
- Must not approve or merge

## 5. Permission Matrix

| Operation | Implementer | Validator | PM | GitHub Agent | Supervisor | PO/Carlos |
|-----------|-------------|-----------|----|-------------|------------|-----------|
| Local commit | ✅ Allowed | ✅ Allowed | ✅ Allowed | N/A | ❌ No | N/A |
| git push (remote) | ❌ No | ❌ No | ❌ No | ✅ When authorised | ❌ No | ❌ (delegates) |
| PR creation | ❌ No | ❌ No | ❌ No | ✅ When authorised | ❌ No | ❌ (delegates) |
| PR merge | ❌ No | ❌ No | ❌ No | ✅ When PO-approved | ❌ No | ✅ PO approval |
| PR comment | ❌ No | ✅ When authorised | ❌ No | ✅ When authorised | ❌ No | ✅ |
| Formal GitHub review | ❌ No | ✅ When authorised | N/A | ❌ No | ❌ No | ✅ |
| Label management | ❌ No | ❌ No | ❌ No | ✅ When authorised | ❌ No | ✅ |
| Branch protection changes | ❌ No | ❌ No | ❌ No | ❌ No | ❌ No | ✅ PO approval |
| Read repo state | ✅ Allowed | ✅ Allowed | ✅ Allowed | ✅ Allowed | ✅ Allowed | ✅ Allowed |

### 5.1 Fixed Workspace Constraint
All agents are bound to their fixed workspace path. Remote GitHub operations must originate from the correct fixed workspace. A push or PR attempt from a wrong or unverified workspace path is a workflow violation regardless of role.

## 6. Allowed and Forbidden Operations
### Allowed
- local git commits in the fixed workspace (all execution roles)
- branch push under explicit PM/PO approval (GitHub Agent only)
- PR creation under explicit PM/PO approval (GitHub Agent only)
- PR merge under explicit PO approval (GitHub Agent only — routed by PM)
- checks reporting (GitHub Agent)
- PR comments and review requests when explicitly authorised (Validator, GitHub Agent)
- formal GitHub review when explicitly authorised (Validator)
- merge review coordination (PM)

### Forbidden
- any git push, PR creation, or merge by implementer, validator, supervisor, or PM
- PM writing to GitHub directly (PM coordinates and approves; GitHub Agent executes)
- PM executing GitHub Agent binaries locally (e.g. `bin/gh-agent`) — PM must route to ELIS GitHub
- PM accessing or referencing GitHub Agent credential files (e.g. `/opt/elis/secrets/github-agent.env`)
- Supervisor writing to GitHub (read-only monitoring role)
- Supervisor executing PR merges — Supervisor is escalation only, not the normal merge actor
- direct merge without Carlos/PO approval (all roles)
- unauthorised PR mutation (any role)
- unauthorised label or comment actions (any role)
- actions from stale, wrong, or unverified fixed workspace identity (any role)
- bypassing protected-branch rules (any role)
- merging from the fixed implementer or validator workspace (implementer, validator)

## 7. PR / Check / Merge Gates
A GitHub write operation is permitted only when:
1. PE is active and scoped in CURRENT_PE.md
2. Agent fixed workspace identity is verified (pwd + git rev-parse --show-toplevel matches assigned path)
3. Branch and commit context match the PE
4. Required evidence packet is present (see §8)
5. The requested action is within the role boundary (see §5)
6. Merge has explicit Carlos/PO approval

Merge never occurs without explicit Carlos/PO approval. Gate 2 does not auto-merge.

## 8. Evidence Packet
Every GitHub write operation must have a compact evidence packet including:
- PE_ID
- role and agent identity (surface name, e.g. `infra-impl-b`)
- fixed workspace path
- branch name
- commit SHA or PR number
- requested GitHub action
- gate status
- approval status
- fallback state, if any
- acting GitHub login
- token/credential source, if applicable
- CI/check status for PR/merge operations
- PR URL for PR operations
- merge SHA for merge operations
- timestamp and operator/session reference

## 9. Manual Fallback Path
When automation fails:
- preserve the attempted state and evidence
- do not silently retry across roles
- escalate to PM for fallback selection
- use the least-privilege manual path available
- keep Carlos/PO approval as the merge gate

## 10. Error / Risk Handling
- Discord exec approval loops are runtime-envelope issues, not GitHub self-review failures.
- GitHub protected-branch and bot-identity failures are separate risks and must be reported distinctly.
- Any identity mismatch, stale branch, or ambiguous authorisation state blocks the operation.
- Fixed workspace path mismatch blocks all GitHub operations, including local commits, until verified.

## 11. Non-goals
- no OpenClaw config changes
- no automatic merge authority
- no implementation of GitHub automation outside this governance model
- no revision of unrelated PE rules

## 12. Cross-References
- `docs/governance/ELIS_PE_Operating_Protocol.md` (worktree rules, fixed workspace model, Supervisor role, Fixed Workspace Binding Certificate, wrong-worktree quarantine)
- `docs/governance/ELIS_Worktree_Preflight_Checklist.md` (path verification, binding certificate)
- `docs/governance/ELIS_PE_Dispatch_Checklist.md` (dispatch readiness)
- `docs/decisions/ADR-011-github-actions-authority-for-portable-gates.md`
- `docs/governance/ELIS_Discord_PO_PM_Checkpoint_Governance.md`
- `docs/ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md` (deterministic enforcement reference)
- `docs/ops/github-agent/GITHUB_AGENT_RULES.md` (failure class registry)

## 13. Version History

| Version | Date       | Author | Changes |
|---------|------------|--------|---------|
| 1.4     | 2026-06-04 | infra-impl-b | Add §1.2 deterministic enforcement reference (skill pack); add §1.3 PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED formal finding with read-only audit table; update cross-references. |
| 1.3     | 2026-06-01 | PM     | Clarify PR merge routing: GitHub Agent executes merges when PO-approved; PM must not execute `bin/gh-agent` locally or access credential files; Supervisor is escalation only. Update permission matrix PR merge row, §4.4, Allowed/Forbidden sections. |
| 1.2     | 2026-05-07 | PM     | Add Supervisor role to permission matrix. Resolve PM GitHub write conflict: PM must not write to GitHub directly; only GitHub Agent may write after explicit PM/PO approval. Update Allowed/Forbidden sections. |
| 1.1     | 2026-05-06 | PM     | Adopt fixed workspace model. Replace bot-centric model with role-based permission matrix. Clarify no-default-write principle. Gate 2 no longer auto-merges. |
| 1.0     | 2026-05-03 | PM     | Initial GitHub Agent operating model. |
