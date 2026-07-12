# ELIS GitHub Operations Skill Pack

**Status:** Canonical — v1.0
**Date:** 2026-06-04
**Owner:** ELIS GitHub Agent (enforced by GitHub Agent runtime)
**Applies to:** ELIS GitHub Agent, PM (coordination), Supervisor (read-only monitoring)

## Purpose

This document defines the deterministic skill-and-rule pack governing all GitHub
operations within the ELIS multi-agent system. Each entry specifies a named skill or
rule, its trigger condition, the required checks and steps, the expected output or
evidence, and the failure class(es) it guards against.

All 22 skills/rules herein are enforceable by the ELIS GitHub Agent runtime.
The first 14 originate from PR #471 (10 classes) plus Phase 1 discovery
(1 class: `STALE_LOCAL_WORKSPACE_HEAD`), as documented in
`docs/ops/github-agent/GITHUB_AGENT_RULES.md` and
`docs/governance/ELIS_GitHub_Agent_Operating_Model.md`.

8 additional governance rules were added during the `elis-core` migration:
- `CORRECT_REPOSITORY_TARGET_RULE`, `WRONG_REPO_PR_RECOVERY_RULE`,
  `LOST_FINAL_RESPONSE_RECOVERY_RULE`, `PROVENANCE_SPLIT_RULE`,
  `WHOLE_WORKTREE_CONTAMINATION_RULE`, `CURRENT_HEAD_VALIDATION_RULE`,
  `CORRECT_BASE_BRANCH_RULE`, `SUPERSEDED_PR_CLOSEOUT_RULE`
— see `docs/ops/github-agent/GITHUB_AGENT_RULES.md` §Rules for definitions.

---

## Skill 1: ELIS_GITHUB_BINDING_PREFLIGHT_SKILL

**Trigger:** Before any GitHub operation (push, PR, merge, label, comment, review,
check re-run).

**Required checks/steps:**
1. Resolve `pwd` and compare against the expected fixed worktree path for the active
   role (e.g. `/opt/elis/agent-worktrees/github-agent`).
2. Run `git remote get-url origin` and verify it matches the canonical ELIS repository
   remote URL.
3. Run `git rev-parse --show-toplevel` and verify it resolves to the expected worktree
   path (not a subdirectory, not a standalone clone).
4. Run `git rev-parse HEAD` and capture the current commit SHA for evidence.
5. Confirm the resolved GitHub identity matches the governed ELIS GitHub identity
   (`app/elis-github` or `elis-git-bot` — never `rochasamurai` except under explicit
   PO-authorised break-glass).

**Expected output/evidence:**
- Worktree path match: PASS/FAIL
- Remote URL match: PASS/FAIL
- Top-level match: PASS/FAIL
- HEAD SHA (evidence only — no credential content)
- GitHub identity match: PASS/FAIL

**Failure class(es) guarded:**
- `WRONG_GITHUB_WORKTREE_OR_CLONE` (class 6)
- `TEMPORARY_HUMAN_GITHUB_AUTH_RISK` / `GITHUB_ACTOR_MISMATCH` (GitHub Agent
  Operating Model §4.4b)

---

## Skill 2: ELIS_GITHUB_BRANCH_LOCK_PREFLIGHT_RULE

**Trigger:** Before `git checkout` or `git switch` to any branch that could be checked
out in another worktree.

**Required checks/steps:**
1. Run `git worktree list` from the canonical repo (`/opt/elis/repo`).
2. Parse output for the target branch name in any worktree path other than the current
   one.
3. If the branch is found in another worktree, block the checkout immediately.
4. Log the conflicting worktree path, branch name, and HEAD SHA for diagnostic
   evidence (no credential content).

**Expected output/evidence:**
- Worktree list output (paths only — no credential content)
- Branch lock status: FREE / LOCKED_BY_OTHER_WORKTREE
- If LOCKED: conflicting path, branch, HEAD SHA

**Failure class(es) guarded:**
- `PE_BRANCH_LOCKED_BY_OTHER_WORKTREE` (class 3)

---

## Rule 3: ELIS_GITHUB_LINKED_WORKTREE_BRANCH_RELEASE_RULE

**Trigger:** When `ELIS_GITHUB_BRANCH_LOCK_PREFLIGHT_RULE` reports that the target
branch is locked in another worktree and the operation cannot proceed without
releasing it.

**Required checks/steps:**
1. Identify the worktree that currently holds the locked branch.
2. Verify the worktree has no uncommitted changes (`git status -sb` must be clean).
3. Push any committed changes on the locked branch to its remote tracking branch
   (if not already pushed).
4. Remove the worktree entry via `git worktree remove <path>`.
5. Verify `git worktree list` no longer shows the released branch.
6. Only then may the target worktree check out the released branch.
7. All steps require explicit PM/PO approval before execution — this is not an
   automatic release.

**Expected output/evidence:**
- Status check on locked worktree: CLEAN / DIRTY
- Push confirmation (if needed): SHA pushed + remote branch
- Worktree removal confirmation
- Post-removal worktree list
- PM/PO approval reference

**Failure class(es) guarded:**
- `PE_BRANCH_LOCKED_BY_OTHER_WORKTREE` (class 3 — recovery path)

---

## Rule 4: ELIS_GITHUB_STALE_LOCAL_BRANCH_HEAD_RULE

**Trigger:** Before any git push, PR creation, or merge based on a local feature branch.

**Required checks/steps:**
1. Run `git fetch origin` to ensure remote tracking branches are current.
2. For a feature branch: run `git rev-list --count --left-right origin/main..HEAD`
   to detect ahead/behind status.
3. If ahead count > 0 and behind count > 0: branch has diverged — block and require
   `git rebase origin/main`.
4. If behind count > 0 and ahead count == 0: no local commits, branch is purely behind
   — fast-forward with `git rebase origin/main`.
5. **Base-worktree sync subcase (`STALE_LOCAL_WORKSPACE_HEAD`):** If the current
   workspace has a detached HEAD behind `origin/main`, sync via
   `git switch --detach origin/main` to move the detached HEAD forward.
6. Verify the branch or detached HEAD is now at the current `origin/main`.

**Expected output/evidence:**
- `git rev-list --count --left-right origin/main..HEAD` output
- Staleness status: CURRENT / BEHIND / DIVERGED
- Sync action taken (rebase, fast-forward, detached-HEAD sync) or BLOCKED
- Post-sync HEAD SHA

**Failure class(es) guarded:**
- `STALE_LOCAL_PE_BRANCH_HEAD` (class 4)
- `STALE_LOCAL_WORKSPACE_HEAD` (class 11 — base-worktree sync subcase)

---

## Rule 5: ELIS_GITHUB_PUSH_PR_UPDATE_SKILL

**Trigger:** Authorised git push or PR update by the ELIS GitHub Agent after PM/PO
approval.

**Required checks/steps (in order):**
1. Execute `ELIS_GITHUB_BINDING_PREFLIGHT_SKILL` (Skill 1) — must PASS.
2. Execute `ELIS_GITHUB_STALE_LOCAL_BRANCH_HEAD_RULE` (Rule 4) — must be CURRENT or
   recently synced.
3. Verify explicit PM/PO approval is recorded (evidence: PM/PO message reference or
   approval packet).
4. Confirm the push target is a feature branch, not `main` (see Rule 10).
5. Execute `git push origin <branch>` using the `bin/gh-agent` wrapper.
6. Capture the post-push SHA from `git rev-parse HEAD`.

**Expected output/evidence:**
- Binding preflight result: PASS
- Stale-head check result: CURRENT / SYNCED
- PM/PO approval reference
- Push command executed (via `bin/gh-agent`)
- Post-push HEAD SHA

**Failure class(es) guarded:**
- `WRONG_GITHUB_WORKTREE_OR_CLONE` (class 6)
- `STALE_LOCAL_PE_BRANCH_HEAD` (class 4)
- `PE_BRANCH_LOCKED_BY_OTHER_WORKTREE` (class 3)
- `PM_WRONG_RESPONSIBILITY_BOUNDARY` (class 1 — PM must not push directly)
- `LOCAL_UNPUSHED_COMMITS_BLOCK_RESET` (class 5)

---

## Rule 6: ELIS_GITHUB_PR_CREATION_SKILL

**Trigger:** Creation of a new pull request on GitHub by the ELIS GitHub Agent.

**Required checks/steps (in order):**
1. Execute `ELIS_GITHUB_BINDING_PREFLIGHT_SKILL` (Skill 1) — must PASS.
2. Execute `ELIS_GITHUB_STALE_LOCAL_BRANCH_HEAD_RULE` (Rule 4) — must be CURRENT or
   recently synced.
3. Verify that CI checks on the current HEAD SHA are green (see Rule 7).
4. Verify explicit PM/PO approval is recorded.
5. Run `gh pr create` via `bin/gh-agent` wrapper with title, body, base branch, and
   label metadata.
6. Capture PR URL and PR number from the command output.

**Expected output/evidence:**
- Binding preflight: PASS
- Stale-head check: CURRENT / SYNCED
- CI status on current HEAD: GREEN (all required checks pass)
- PM/PO approval reference
- PR URL and PR number
- PR body content (relevant metadata — no credentials)

**Failure class(es) guarded:**
- `STALE_CHECK_RUN_NOT_CURRENT_HEAD` (class 7)
- `STALE_LOCAL_PE_BRANCH_HEAD` (class 4)
- `PM_WRONG_RESPONSIBILITY_BOUNDARY` (class 1)
- `PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED` (class 2)

---

## Rule 7: ELIS_GITHUB_CHECKS_MONITORING_SKILL

**Trigger:** Before PR creation, before PR merge, and periodically during validation
(Supervisor monitoring).

**Required checks/steps:**
1. Run `gh run list --branch <branch> --limit 10 --json headSha,databaseId,event,conclusion,workflowName`
   (read-only, via `gh` directly or `bin/gh-agent` — permitted under §4.4b).
2. Filter runs to the current HEAD SHA only.
3. For each matching run, extract: SHA, run ID (databaseId), event type, conclusion,
   and required/blocking flag.
4. If any run matches an older SHA, report it as stale and exclude from the conclusion.
5. Determine overall CI status: GREEN (all required runs on current SHA pass),
   FAILING (any required run on current SHA fails), PENDING (runs still in progress).

**Expected output/evidence:**
- Report table: SHA | Run ID | Event | Conclusion | Required/Blocking
- Staleness note if any runs excluded
- Overall CI status: GREEN / FAILING / PENDING

**Failure class(es) guarded:**
- `STALE_CHECK_RUN_NOT_CURRENT_HEAD` (class 7)

---

## Rule 8: ELIS_GITHUB_PROTECTED_FILES_RULE

**Trigger:** Before any git commit that modifies repository governance files.

**Protected files list (only PM may edit):**
- `CURRENT_PE.md`
- `AGENTS.md` (governance sections — §2.12, §3, §5, §10, §14)
- `docs/governance/ELIS_GitHub_Agent_Operating_Model.md`
- `docs/governance/ELIS_PE_Operating_Protocol.md`
- `docs/governance/ELIS_Agent_Dispatch_Binding_and_Validation_Rules.md`

**Required checks/steps:**
1. Run `git diff --name-status origin/main..HEAD` (or against the base branch).
2. Compare modified files against the protected files list.
3. If a protected file is modified and the committer is not the PM or PO, flag a
   `PM_WRONG_RESPONSIBILITY_BOUNDARY` violation.
4. Block the commit or push and report to PM.

**Expected output/evidence:**
- Scope diff output
- Protected files modified (if any)
- Violation status: PASS / VIOLATION
- If VIOLATION: actor identity + file list

**Failure class(es) guarded:**
- `PM_WRONG_RESPONSIBILITY_BOUNDARY` (class 1)

---

## Rule 9: ELIS_GITHUB_NO_SECRET_OUTPUT_RULE

**Trigger:** Before any output is written to evidence, status packets, HANDOFF, REVIEW,
chat messages, or command-line diagnostic output.

**Required checks/steps:**
1. Scan output text for patterns matching secrets:
   - GitHub tokens (`ghp_*`, `gho_*`, `ghu_*`, `ghs_*`, `ghr_*`)
   - API keys (`sk-*` for OpenAI/Anthropic-style)
   - Private key markers (`-----BEGIN.*PRIVATE KEY-----`)
   - Credential environment variable values (e.g. after `=` in env output)
   - Any file content from `/opt/elis/secrets/` paths
2. If any pattern matches, redact the output or replace with a safe summary:
   - Token/credential values → `***REDACTED***`
   - Secret content → path reference only (e.g. `secrets file at /opt/elis/secrets/X`)
3. Never include credential content in any evidence block. Evidence is limited to:
   - File paths (without content)
   - Command availability (bin/gh-agent exists: YES/NO)
   - Auth status class (authenticated: YES/NO — never print token identity)
   - Permission class (write-capable: YES/NO)

**Expected output/evidence:**
- Sanitised output with no secret content
- If redaction occurred: count of patterns redacted (not the values themselves)

**Failure class(es) guarded:**
- `SECRET_OUTPUT_RISK` (class 10)

---

## Rule 10: ELIS_GITHUB_NO_DIRECT_MAIN_PUSH_RULE

**Trigger:** Before any `git push` operation.

**Required checks/steps:**
1. Verify the push target branch is not `main` or `master`.
2. Verify the push is not a force-push (no `--force` or `+branch` refspec).
3. Confirm all changes to `main` enter only via PR.
4. If the target is `main` or force-push is detected, block immediately and report.

**Expected output/evidence:**
- Target branch in push refspec
- Force-push flag: PRESENT / ABSENT
- Push eligibility: ALLOWED / BLOCKED (direct main push)
- If BLOCKED: reason + escalation path

**Failure class(es) guarded:**
- `PM_WRONG_RESPONSIBILITY_BOUNDARY` (class 1)
- `PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED` (class 2)

---

## Rule 11: ELIS_GITHUB_NO_MERGE_WITHOUT_PO_APPROVAL_RULE

**Trigger:** Before any PR merge operation by the GitHub Agent or any agent.

**Required checks/steps:**
1. Run `ELIS_GITHUB_CHECKS_MONITORING_SKILL` (Rule 7) — CI must be GREEN on current
   HEAD.
2. Verify the PR does not have the `pm-review-required` label.
3. Verify explicit PO approval is recorded and linked.
4. Verify the PR is not merged by an agent that lacks merge authority (implementer,
   validator, supervisor — all blocked).
5. If all checks pass, execute `gh pr merge <number> --merge --subject <title>`
   via `bin/gh-agent`.
6. Record the merge SHA and merged-at timestamp.

**Expected output/evidence:**
- CI status: GREEN
- `pm-review-required` label: ABSENT
- PO approval reference
- Merge command executed via `bin/gh-agent`
- Merge SHA + merged-at timestamp
- PR URL

**Failure class(es) guarded:**
- `PM_WRONG_RESPONSIBILITY_BOUNDARY` (class 1 — PM must not merge)
- `PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED` (class 2)
- `STALE_CHECK_RUN_NOT_CURRENT_HEAD` (class 7)

---

## Rule 12: ELIS_GITHUB_COMMIT_AUTHORSHIP_PRESERVATION_RULE

**Trigger:** Before any git operation that commits or pushes changes authored by an
ELIS agent.

**Required checks/steps:**
1. Verify that implementation commits are authored by the implementer role
   (e.g. `infra-impl-b`, author email `elis-git-bot@electoralintegrity.org`).
2. Verify that REVIEW commits are authored by the validator role.
3. For ELIS GitHub Agent branch manipulation (push, rebase, sync): verify that
   existing commit authorship is preserved — the GitHub Agent must not rewrite
   or squash author attribution.
4. If author attribution would be lost or altered, block the operation.

**Expected output/evidence:**
- Author attribution check: PRESERVED / WOULD_BE_ALTERED
- If altered: list of affected commits + current and would-be authors

**Failure class(es) guarded:**
- `PM_WRONG_RESPONSIBILITY_BOUNDARY` (class 1)
- All failure classes that imply authorship confusion

---

## Rule 13: ELIS_GITHUB_SAFE_ROLLBACK_RULE

**Trigger:** When a PR must be rolled back (closed without merge, or reverted after
merge).

**Required checks/steps:**
**Before merge (close PR + delete branch):**
1. Verify PO approval is recorded for the rollback.
2. Close the PR via `gh pr close <number>` using `bin/gh-agent`.
3. Delete the branch via `git push origin --delete <branch>` using `bin/gh-agent`.
4. Verify the PR is closed and branch deleted.

**After merge (revert):**
1. Verify PO approval is recorded for the revert.
2. Create a revert commit via `git revert <merge-sha>` in the GitHub Agent worktree.
3. Push the revert to a new branch.
4. Open a new PR for the revert (requires all standard merge gates).
5. No runtime credential or config rollback is expected — revert is source-code only.

**Expected output/evidence:**
- PO approval reference
- Rollback action taken (close PR, delete branch, or revert commit)
- Evidence of action (PR close confirmation, branch deletion confirmation, revert SHA)
- New PR URL (for post-merge revert)

**Failure class(es) guarded:**
- `PM_WRONG_RESPONSIBILITY_BOUNDARY` (class 1)
- `PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED` (class 2)

---

## Rule 14: ELIS_GITHUB_PR_CLOSEOUT_PACKET_RULE

**Trigger:** After a PR is merged or closed, as part of the PE closeout report.

**Required checks/steps:**
1. Capture the merge SHA from `gh pr view <number> --json mergeCommit` (read-only).
2. Capture the merged-at timestamp from `gh pr view <number> --json mergedAt`.
3. Confirm the branch was deleted: `git ls-remote origin <branch>` returns empty.
4. Update the Active PE Registry in `CURRENT_PE.md` to reflect `merged` status.
5. Record the closeout packet in the PE's `.elis/pe/` workspace directory.

**Expected output/evidence:**
- Merge SHA
- Merged-at timestamp (ISO 8601)
- Branch deletion confirmation (remote ref absent)
- Registry update confirmation
- Closeout packet file path and content summary (no credentials)

**Failure class(es) guarded:**
- `PM_WRONG_RESPONSIBILITY_BOUNDARY` (class 1)
- `REVIEW_ARTEFACT_WRONG_PATH` (class 8)
- `REVIEW_SCHEMA_NONCOMPLIANT` (class 9)

---

## Version History

| Version | Date       | Author           | Changes |
|---------|------------|------------------|---------|
| 1.0     | 2026-06-04 | infra-impl-b     | Initial skill pack — 14 skills/rules covering all 11 failure classes |
| 1.1     | 2026-07-12 | elis-github      | Add cross-reference to 8 new governance rules in GITHUB_AGENT_RULES.md; update skill count to 22 |