# GitHub Agent Rules and Source Path Enforcement

## Overview

This document outlines the rules and enforcement mechanisms for the GitHub Agent's PR source path selection process, ensuring deterministic and secure GitHub operations with explicit runtime/worktree separation.

## Rules

### RULE_DEFINED_PR_SOURCE_PATH

The GitHub Agent must select exactly one defined PR source path that is explicitly authorized for the operation, or fail closed if multiple or no valid paths exist.

### GITHUB_AGENT_READS_SOURCE_WRITES_REMOTE

The GitHub Agent reads from the specified PR source path and writes all changes to the remote GitHub repository.

### NO_RUNTIME_WORKSPACE_AS_PR_SOURCE

The GitHub Agent must not default to its runtime workspace as the PR source path. This prevents accidental modifications to the runtime workspace.

### NO_SINGLE_AUTHORISED_PR_SOURCE_PATH_NO_GITHUB_WRITE

The GitHub Agent must not allow operations through a single authorized PR source path that would not enable GitHub writes.

### NO_PREPARED_GITHUB_AGENT_RUNTIME_NO_GITHUB_WRITE

The GitHub Agent must always ensure that any prepared runtime workspace has proper GitHub write capabilities enabled.

### RUNTIME_WORKTREE_SEPARATION_REQUIREMENT

The GitHub Agent must enforce explicit separation between the runtime execution environment and the PR source worktree. The runtime workspace must be different from the source workspace to maintain security boundaries.

### SELF_CONTAINED_STATE_CHANGING_DISPATCH_RULE

For the GitHub Agent specifically, this rule requires:
1. All state changes must originate from the designated and authorized PR source path
2. Runtime and source worktrees must be explicitly validated as different paths
3. Any modification must follow the complete authorization chain through PM/PO
4. All write operations must be audited and traceable to their source
5. The separation is enforced for all GitHub write operations

### CORRECT_REPOSITORY_TARGET_RULE

All GitHub operations must target the correct, PO-approved repository. Operations targeting the wrong repository (e.g., legacy `rochasamurai` repos when `elis-core` is the authorised target) must be blocked. The active repository target is determined by `CURRENT_PE.md` or explicit PO directive.

### WRONG_REPO_PR_RECOVERY_RULE

If a PR is opened against the wrong repository, the agent must:
1. Immediately stop all operations on the wrong-repo PR
2. Report to PM with the PR URL and the correct target
3. Not close the wrong-repo PR until PO authorises the close
4. Create the correct PR in the intended repository only after PO confirmation

### LOST_FINAL_RESPONSE_RECOVERY_RULE

If the GitHub Agent's final response to a dispatch is lost (e.g., Discord drop, timeout), the agent must:
1. Check current GitHub state for any partial operations
2. Report current state to PM/PO with evidence
3. Await explicit instruction before re-attempting the operation
4. Not silently retry the operation

### PROVENANCE_SPLIT_RULE

When porting content from one repository to another (e.g., legacy monorepo → `elis-core`), the agent must:
1. Preserve provenance metadata (source PR, source commit SHA, original author) in commit messages
2. Not carry forward stale validation artefacts, HANDOFF files, or CURRENT_PE.md
3. Replace all legacy repository references with the correct target repository
4. Create a clean branch from the target's current default branch

### WHOLE_WORKTREE_CONTAMINATION_RULE

If the agent's fixed worktree is contaminated (wrong branch, dirty tree, detached HEAD, wrong remote), the agent must:
1. Run the binding preflight check
2. Report contamination to PM with full evidence
3. Not perform any GitHub write operation until contamination is resolved
4. Apply the least-invasive correction (rebase, checkout, or clean as appropriate)

### CURRENT_HEAD_VALIDATION_RULE

Before any GitHub write operation, the agent must validate that the current HEAD SHA corresponds to the expected commit for the active PE. If HEAD does not match the expected SHA, the agent must:
1. Report the mismatch to PM
2. Run CI status check
3. Not proceed until HEAD is confirmed correct

### CORRECT_BASE_BRANCH_RULE

All feature branches must be created from the correct base branch as declared in CURRENT_PE.md. The agent must verify:
1. The base branch exists and is up to date with origin
2. The new branch is created from the tip of the base branch
3. The base branch is not a feature branch (no chain-branching unless explicitly authorised)

### SUPERSEDED_PR_CLOSEOUT_RULE

When a new PR supersedes an older PR (e.g., porting content to a different repository), the agent must:
1. Not close the superseded PR unless PO explicitly authorises it
2. Post a supersession comment on the old PR referencing the new PR URL
3. Record the supersession in the new PR description
4. Preserve the old PR as read-only evidence

## PR Source Path Selection Process

1. Validate all potential PR source paths to determine exactly one authorized source
2. Fail closed if zero or multiple valid sources detected
3. Ensure source path has appropriate write access to the target GitHub repository
4. Block operations that would bypass the defined source path rules
5. Enforce runtime/worktree separation as part of validation process

## Action Types

### open_pr_for_validated_pe_branch

An action type that validates a PE branch and opens a pull request from the predetermined, authorized source path.

## Source Path Resolution Logic

The GitHub Agent uses these precedence rules:
1. Explicitly configured PR source path from the environment
2. PE-specific authorized source path
3. Fails if multiple or no authorized paths identified

## Runtime/Worktree Separation Requirements

### Separation Enforcement

To maintain security boundaries and operational clarity, the GitHub Agent must:

1. **Runtime Isolation**: Verify that the execution environment (runtime) differs from the source worktree
2. **Workspace Verification**: Confirm both environment and source are proper fixed workspaces
3. **Identity Binding**: Ensure agent activation matches workspace identity
4. **Access Controls**: Restrict source workspace from being runtime workspace

### Validation Sequence

For each GitHub operation, the agent must perform the following validation sequence:

1. Determine the runtime worktree location
2. Determine the source worktree location  
3. Verify runtime and source worktrees are distinct paths
4. Validate both worktrees are fixed workspaces
5. Confirm valid git repository state in both workspaces
6. Authenticate agent identity against expected workspace

### Clarification: Runtime ≠ Source Worktree

This requirement applies specifically to GitHub Agent operations as defined in the ELIS GitHub Agent Operating Model. While other agents in the system may not need explicit runtime/source separation (as they may not operate in separate execution environments), the GitHub Agent **must always enforce** this separation to mitigate risks associated with repository manipulation.

### Error Handling

If runtime/worktree separation requirements are not met:
- The operation must fail closed with clear error messaging
- Log validation failure for audit purposes
- Trigger security alert for violation
- Prevent any further processing

---

## Failure Class Registry

The following table documents 11 failure classes identified through PR #471 and
Phase 1 discovery. These classes are the authoritative set that the
`ELIS_GITHUB_OPS_SKILL_PACK.md` (see §Failure Class Enforcement Reference) guards
against.

| # | Class Name | Description | Detection Method | Required Action |
|---|------------|-------------|------------------|-----------------|
| 1 | `PM_WRONG_RESPONSIBILITY_BOUNDARY` | PM performs GitHub write operations (push, PR, merge, label) that belong to the GitHub Agent role, or agents edit governance files reserved for PM | Scope diff (`git diff --name-status`) plus actor identity cross-reference; GitHub audit log for actor mismatch | Block operation; escalate to PO; file scope correction if implemented by wrong actor |
| 2 | `PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED` | PM retains standing GitHub write/merge capability that should be removed or restricted to a documented break-glass path | Read-only audit of PM GitHub-capable paths (shell aliases, `gh` auth status, git credentials); evidence = paths and availability only, no credential content | Record formal finding; defer actual credential restriction to PE-OPS-GITHUB-PERMISSIONS-01 |
| 3 | `PE_BRANCH_LOCKED_BY_OTHER_WORKTREE` | A branch that needs to be checked out is already checked out in a different Git worktree, preventing the checkout | `git worktree list` shows the branch in a non-current worktree | Run ELIS_GITHUB_LINKED_WORKTREE_BRANCH_RELEASE_RULE (Skill Pack Rule 3) with PM/PO approval |
| 4 | `STALE_LOCAL_PE_BRANCH_HEAD` | The local PE feature branch is behind `origin/main`, meaning it would push stale code | `git fetch origin` followed by `git rev-list --count --left-right origin/main..HEAD` shows behind count > 0 | Rebase onto `origin/main`; re-run CI on updated HEAD |
| 5 | `LOCAL_UNPUSHED_COMMITS_BLOCK_RESET` | Local commits exist on a branch that are not present on the remote, blocking workspace reset | `git log origin/<branch>..HEAD` returns non-empty | Push commits before reset, or stash/archive if workspace reset is the goal |
| 6 | `WRONG_GITHUB_WORKTREE_OR_CLONE` | The current working directory is not the correct fixed worktree, or the git remote does not match the canonical repo | `pwd` and `git rev-parse --show-toplevel` mismatch; `git remote get-url origin` mismatch | Run ELIS_GITHUB_BINDING_PREFLIGHT_SKILL (Skill Pack Skill 1); switch to correct worktree or re-clone in correct location |
| 7 | `STALE_CHECK_RUN_NOT_CURRENT_HEAD` | CI check runs exist but correspond to an older commit SHA, not the current HEAD | `gh run list --branch <branch>` filtered by SHA does not include current HEAD | Re-run CI on current HEAD; do not create or merge PRs against stale runs |
| 8 | `REVIEW_ARTEFACT_WRONG_PATH` | A REVIEW file is placed in a directory that does not match the governing standard (e.g. outside `.elis/pe/<PE-ID>/`) | File path pattern match against `REVIEW_PE<N>.md` in the expected location | Move file to correct path; commit path correction before validator start |
| 9 | `REVIEW_SCHEMA_NONCOMPLIANT` | A REVIEW file is missing required sections or fails the governing schema | Schema validation check (e.g. grep for `### Evidence`, `### Verdict`, `### Failure classes addressed` headings) | Add missing sections; re-commit before review submission |
| 10 | `SECRET_OUTPUT_RISK` | Evidence, diagnostic output, or status packets contain credential content, tokens, secret keys, or private key material | Pattern scan for `ghp_*`, `sk-*`, `BEGIN.*PRIVATE KEY`, file content from `/opt/elis/secrets/` | Redact immediately; do not include in any output; report occurrence to PM without exposing the value |
| 11 | `STALE_LOCAL_WORKSPACE_HEAD` | The fixed agent workspace has a detached HEAD that is behind `origin/main`, causing base misalignment | `git rev-list --count HEAD..origin/main` in detached HEAD state shows behind count > 0 | Run `git switch --detach origin/main` to sync detached HEAD; then rebase any PE branch onto it |

### Failure Class Enforcement Reference

All 11 failure classes above are addressed by the deterministic enforcement rules
in `docs/ops/github-agent/ELIS_GITHUB_OPS_SKILL_PACK.md`. That document contains
14 skills and rules that implement detection, blockage, and recovery for every class.

---

## PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED — Formal Finding

**Status:** Open — Finding recorded 2026-06-04
**Source:** PE-OPS-GITHUB-SKILLS-01
**Target PE for remediation:** PE-OPS-GITHUB-PERMISSIONS-01

**Issue:** The PM role currently retains standing GitHub write/merge capability via
its `gh` CLI authentication and/or shell-level `git push` access. Per the operating
model (§4.3 of `ELIS_GitHub_Agent_Operating_Model.md`): "PM must not write to GitHub
directly. All GitHub write operations (push, PR, labels, comments) must be executed
by the GitHub Agent after explicit PM approval."

**Target state:** PM should not retain standing GitHub write/merge capability except
a documented, PO-approved break-glass path. This means:
- PM `gh` auth is limited to read-only scope, or removed entirely
- PM has no `git push` capability to the ELIS remote (via credential removal or
  remote URL restriction)
- Break-glass path is documented, approved by PO, and logged when used

**Action taken in this PE:** Finding recorded in the operating model and this file.
Actual credential restriction/removal is **out of scope** and deferred to
`PE-OPS-GITHUB-PERMISSIONS-01` by explicit plan instruction.

---

## PM Role-Boundary Rule

Per the ELIS GitHub Agent Operating Model (§4.3, §4.4, §5):

**PM coordinates; ELIS GitHub executes.**

- PM owns PE coordination, authorisation checkpoints, and fallback escalation.
- PM must **not** write to GitHub directly — no `git push`, no `gh pr create`,
  no `gh pr merge`, no `gh label`, no `gh pr close` on production branches.
- PM must **not** execute `bin/gh-agent` locally or access credential files at
  `/opt/elis/secrets/github-agent.env`.
- All GitHub write operations must be routed to the ELIS GitHub Agent (`app/elis-github`)
  via the documented A2A request flow or PM→GitHub Agent dispatch.
- Exception — **PO-approved break-glass:** Only the PO (Carlos Rocha) may authorise a
  direct PM write operation, and every such operation must be logged with:
  - PO approval reference
  - Exact command executed
  - SHA(s) affected
  - Rationale for break-glass path
  - Timestamp
  - Post-operation boundary reset confirmation