<!-- ELIS_GITHUB_EXECUTION_POLICY_V3 -->
## ELIS GitHub execution policy — AUTHORITATIVE

This policy supersedes ELIS_GITHUB_EXECUTION_POLICY_V2 (broker-mediated
execution) and all older launcher, sudo, `gh-agent`, and `git-agent`
instructions in this profile, effective with the direct-access runtime
migration completed 2026-08-18.

- Runtime identity is **elis-github (uid 995)**.
- Never use `sudo`, `su`, or `runuser` to perform ELIS GitHub operations.
- Never use the legacy `gh-agent`, `git-agent`, `git-credential-gh-agent`
  wrappers, or the retired `gh-agent-client` -> `gh-agentd` broker path.
- The GitHub App private key remains accessible only to root / the
  `elis-github-secrets` group; this Hermes agent must never read or
  handle that credential directly, under V2 or V3.
- **Canonical execution path:** direct `gh`/`git`, via the approved
  elis-github wrappers (this service's own environment only), using the
  current short-lived GitHub App installation token (read fresh from
  `/run/elis-github/github-token` on every invocation).
- Ordinary authorized GitHub operations — clone/fetch/pull, branch
  creation/deletion, commits, push, repository content updates, PR
  create/update/close, PR merge (when explicitly authorized),
  workflow-file changes, Actions read, Actions rerun, release operations
  (when explicitly authorized) — may be performed directly. **No
  purpose-built broker operation is required** for any ordinary
  authorized write. `pr1-publish` was V2's single frozen write operation
  and is not the gate for ordinary writes under V3.
- Authorization = PO/ELIS governance directive AND GitHub App repository
  scope AND GitHub App granted permissions AND repository
  rules/CI/branch protection. All four must permit an operation. Task
  scope, the Operation Tiers below, and every other governance rule in
  this document still apply exactly as before — this policy changes
  *how* an authorized write executes, not *whether* it is authorized.
- **Current authorized repositories:** `elis-core/elis-core` and
  `elis-core/elis-research`, per the GitHub App installation token. Do
  not infer authority over any repository outside that set.
- **Administration is unavailable** — the GitHub App is not granted
  Administration. Do not add, simulate, or work around this.
- `gh-agentd` has been physically decommissioned (2026-08-22) and is no
  longer available in any capacity, including rollback. The retired
  `gh-agent-client` -> `gh-agentd` broker path must never be assumed,
  referenced, or waited on. Do not report "purpose-built gh-agentd
  operation required" as a reason to block an otherwise-authorized
  ordinary operation — a legitimate BLOCKED result must instead cite:
  missing GitHub App permission; repository outside token scope; a
  GitHub ruleset/branch-protection rejection; absent PO/task
  authorization; an unhealthy direct wrapper/token path; or the active
  task's scope forbidding the mutation.
- There is no fallback to personal GitHub credentials or the `samurai`
  identity.

---
name: github
description: "Complete GitHub workflow: auth setup, PR lifecycle, code review, issues, repository management, and CI monitoring. Umbrella for the former github-* skills."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, PR, Code-Review, Issues, Repo-Management, CI/CD, Auth]
---

# GitHub Workflow Umbrella

Complete toolkit for working with GitHub: authentication, pull requests, code review, issues, repository management, CI monitoring, and release management. Each section below covers a major workflow area.

**Scope note for the production `elis-github` profile:** the reference material below is general GitHub-workflow documentation and is broader than any single operation this profile performs. Every command remains subject to **ELIS_GITHUB_EXECUTION_POLICY_V3**, the active operation tiers, and the current repository scope (`elis-core/elis-core`, `elis-core/elis-research`) defined in `SOUL.md` — a command's presence below documents general GitHub capability, not ELIS authorization to run it.

## Authentication Model (Production elis-github)

This profile has exactly **one** executable authentication model: the approved elis-github `gh`/`git` wrappers, authenticated via the current short-lived GitHub App installation token (see **ELIS_GITHUB_EXECUTION_POLICY_V3** above). The wrappers resolve identity and repository scope themselves — there is no owner/repo auto-detection or credential-fallback boilerplate for this profile to run.

---

## 1. Authentication Setup

`references/github-auth.md` is **LEGACY / SUPERSEDED historical reference material** — do not execute any command it contains. It covers (historically) SSH, GitHub App token launcher, credential contamination detection, safe.directory pitfalls, and cross-user git permissions. Current execution authority is **ELIS_GITHUB_EXECUTION_POLICY_V3** (above): use only the approved elis-github `gh`/`git` wrappers with the current short-lived GitHub App installation token.

The generic setup methods below (`gh auth login`, `credential.helper store`, personal SSH keys, `git config --global user.*`) are **NON-EXECUTABLE generic reference only** — they describe how GitHub auth works in general, not an authorized action for this production profile. This profile must never run any of them: there is no personal-credential, generic-`GITHUB_TOKEN`, or `~/.git-credentials`/`~/.hermes/.env` fallback path.

### Generic Setup Methods (reference only — not for this profile)

| Method | Command |
|--------|---------|
| gh auth (browser) | `gh auth login` |
| gh auth (token) | `echo "$TOKEN" \| gh auth login --with-token` then `gh auth setup-git` |
| Git HTTPS (token) | `git config --global credential.helper store`, then enter token as password on first `git push` |
| Git SSH | Generate key: `ssh-keygen -t ed25519`, add to github.com/settings/keys |
| Git identity | `git config --global user.name "Name" && git config --global user.email "email"` |

---

## 2. Pull Request Lifecycle

`references/github-pr-workflow.md` is **LEGACY / SUPERSEDED historical reference material** — do not execute any command it contains. It covers (historically) branch creation pitfalls (scope contamination, worktree awareness), PO pre-push verification, pre-merge identity audit, CI monitoring & auto-fix, merge methods, and post-merge cleanup. Current execution authority is **ELIS_GITHUB_EXECUTION_POLICY_V3** (above), using the approved elis-github `gh`/`git` wrappers with the current short-lived GitHub App installation token.

### Quick Reference

```bash
# Branch from origin/main (NOT from current HEAD)
git fetch origin main
git checkout -b feat/description origin/main

# Commit
git add <files>
git commit -m "feat: description"

# Push and create PR (draft — Tier 1)
git push -u origin HEAD
gh pr create --draft --title "feat: description" --body "## Summary" --base main

# Take out of draft when ready (Tier 1)
gh pr ready <N>

# Verify PR
gh pr view <N> --json number,headRefName,baseRefName,state,files,url

# Monitor CI
gh pr checks --watch

# Merge — Tier 2: requires explicit PO approval naming this exact PR number
gh pr merge <N> --squash --delete-branch
```

### Common Pitfalls
- **Branch from wrong base:** `git checkout -b <name>` without explicit origin base inherits previous branch commits
- **Worktree locked:** `git checkout <branch>` fails with "already used by worktree" — switch to the owning worktree
- **safe.directory:** First git operation through a restricted wrapper may fail — configure via the same wrapper
- **Harmless local ref error:** if a push succeeds remotely but the local tracking ref update fails with Permission denied, verify with `git ls-remote` — this can occur with any cross-identity execution path, including the current elis-github wrapper.
- **Execution path:** use only the approved elis-github `gh`/`git` wrappers with the current short-lived GitHub App installation token (ELIS_GITHUB_EXECUTION_POLICY_V3). Never use the retired `gh-agent`, `git-agent`, or `gh-agent-client`/`gh-agentd` broker path, and never use `sudo` to change GitHub identity. An operation outside the GitHub App's granted permissions/repository scope, or outside the active task's authorized scope, must fail closed and be escalated to PO — not routed to a purpose-built broker operation, which is no longer the gate.
- **Cross-user copy fails:** When staging source is under `/home/samurai/` (mode 750) and `elis-github` is not in the `samurai` group, direct copy as `elis-github` fails. Check permissions first: `stat -c '%a %A %U:%G' /home/samurai` + `groups elis-github`. Use a PO-authorised staging bridge under a world-traversable path if blocked.
- **`git --work-tree=<path> add -A` stages deletions:** If the alternate work tree lacks files tracked in the index, `--work-tree` + `add -A` treats them as deleted. Only use `--work-tree` when the alternate tree is a complete superset of the index. For staged populations, copy files into the actual worktree first.

---

## 3. Code Review

See `references/github-code-review.md` for full review workflow including local pre-push review, PR review with inline comments, review checklist, and formal review submission (approve/request-changes/comment).

### Local Review (Pre-Push)

```bash
# Scope
git diff main...HEAD --stat
git log main..HEAD --oneline

# Full diff
git diff main...HEAD

# File-by-file
git diff main...HEAD -- src/file.py

# Quick checks
git diff main...HEAD | grep -n "print(\|console\.log\|TODO\|FIXME\|debugger"
git diff main...HEAD | grep -in "password\|secret\|api_key\|token.*="
```

### PR Review

```bash
# Set up
git fetch origin pull/<N>/head:pr-<N>
git checkout pr-<N>
```

Formal review-verdict submission (`gh pr review --approve` / `--request-changes`) is **Tier 3 — always denied** for this profile (see `SOUL.md` Hard Limits / Operation Tiers). Do not run these commands. Inline comments that do not constitute a formal approve/request-changes verdict remain subject to the active handoff envelope's tier.

---

## 4. Issues Management

See `references/github-issues.md` for full details including creating/viewing issues, labels, assignment, commenting, closing/reopening, triage workflows, and bulk operations.

### Quick Reference

| Action | gh | REST reference |
|--------|-----|------|
| List issues | `gh issue list` | `GET /repos/o/r/issues` (read-only) |
| Create issue | `gh issue create --title "..." --body "..." --label "bug"` | — |
| Add labels | `gh issue edit N --add-label "bug"` | — |
| Assign | `gh issue edit N --add-assignee user` | — |
| Comment | `gh issue comment N --body "..."` | — |
| Close | `gh issue close N` | — |

Direct REST mutation calls (`POST`/`PATCH` against `/repos/o/r/issues*`) are **not an approved alternative execution path under V3** and have been removed from this table rather than shown as a fallback — the only production path is the approved elis-github `gh`/`git` wrappers with the short-lived GitHub App installation token (`ELIS_GITHUB_EXECUTION_POLICY_V3`).

`gh issue comment` and `gh issue close` have no explicit governing tier in `SOUL.md` (Tier 1 covers `gh issue create`/`gh issue edit` only) — do not treat their presence above as authorization; confirm tier classification with PO before use.

---

## 5. Repository Management

See `references/github-repo-management.md` for full details including cloning, creating repos, forking, branch protection, secrets, releases, GitHub Actions workflows, and gists.

### Quick Reference

| Action | gh | git |
|--------|-----|-----|
| Clone | `gh repo clone o/r` | `git clone https://github.com/o/r.git` |
| Create repo | `gh repo create name --public` | — |
| Fork | `gh repo fork o/r --clone` | — |
| Create release | `gh release create v1.0` | — |
| Rerun CI | `gh run rerun ID` | — |

Direct `curl` calls against the GitHub REST API for repository creation, forking, releases, or Actions reruns are **not an approved alternative execution path under V3** (the only production path is the approved elis-github `gh`/`git` wrappers with the short-lived GitHub App installation token, per `ELIS_GITHUB_EXECUTION_POLICY_V3`) and have been removed from this table rather than shown as a fallback.

`gh secret set` / `gh secret delete` are **Tier 3 — always denied** for this profile and are intentionally absent from this table.

`gh repo create` and `gh repo fork` are neither covered by any explicit `SOUL.md` operation tier nor by the "ordinary authorized operations" list in `ELIS_GITHUB_EXECUTION_POLICY_V3` (which covers operations on already-scoped repositories, not creating or forking a repository). This profile's authorized repository scope is fixed to `elis-core/elis-core` and `elis-core/elis-research` — do not treat their presence above as authorization; confirm tier classification and scope applicability with PO before use.

---

## CI Monitoring & Diagnosis

See `references/ci-failure-diagnosis.md` for structured failure diagnosis.

```bash
# Monitor until complete
gh pr checks --watch

# Get failure details
gh run list --branch $(git branch --show-current) --limit 5
gh run view <RUN_ID> --log-failed

# Rerun
gh run rerun <RUN_ID> --failed
```

---

## Deeper Reference Files

- `references/github-auth.md` — **LEGACY / SUPERSEDED historical reference only; do not execute contained commands.** (Historical) full auth setup: HTTPS tokens, SSH, GitHub App token launcher, credential contamination, safe.directory, cross-user git permissions. Current authority: **ELIS_GITHUB_EXECUTION_POLICY_V3** (above).
- `references/github-pr-workflow.md` — **LEGACY / SUPERSEDED historical reference only; do not execute contained commands.** (Historical) full PR lifecycle: branch creation, scope contamination, PO pre-push checks, identity audit, CI monitoring, merge, post-merge cleanup. Current authority: **ELIS_GITHUB_EXECUTION_POLICY_V3** (above).
- `references/github-code-review.md` — Full review workflow: local pre-push, PR review, inline comments, formal review submission
- `references/github-issues.md` — Full issues management: create, view, label, assign, comment, triage, bulk operations
- `references/github-repo-management.md` — Full repo management: clone, create, fork, settings, branch protection, secrets, releases, Actions workflows, gists
- `references/identity-audit-checklist.md` — Pre-merge identity audit for restricted launcher environments
- `references/ci-troubleshooting.md` — CI troubleshooting, especially environment-specific test failures
- `references/gate-c-g4-packet.md` — **LEGACY / SUPERSEDED historical reference only; do not execute contained commands.** (Historical) pre-execution GitHub operation packet (Gate C / G4): 11-section proposal-only format for governed repo population with evidence gathering, rollback plan, and stop conditions. Current authority: **ELIS_GITHUB_EXECUTION_POLICY_V3** (above).
- `references/po-handoff-protocol.md` — PO message.txt handoff protocol
- `references/elis-worktree-layout.md` — ELIS multi-repo layout
- `references/conventional-commits.md` — Commit message format reference
