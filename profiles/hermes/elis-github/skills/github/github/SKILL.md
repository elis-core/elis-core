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

**Common pattern throughout:** Every operation is shown with `gh` CLI first, then a `git` + `curl` fallback for environments without `gh`. Use the auth detection flow below to determine which path to use.

## Auth Detection Boilerplate

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  if [ -z "$GITHUB_TOKEN" ]; then
    if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi

REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
```

---

## 1. Authentication Setup

`references/github-auth.md` is **LEGACY / SUPERSEDED historical reference material** — do not execute any command it contains. It covers (historically) SSH, GitHub App token launcher, credential contamination detection, safe.directory pitfalls, and cross-user git permissions. Current execution authority is **ELIS_GITHUB_EXECUTION_POLICY_V3** (above): use only the approved elis-github `gh`/`git` wrappers with the current short-lived GitHub App installation token.

### Quick Setup

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

# Push and create PR
git push -u origin HEAD
gh pr create --title "feat: description" --body "## Summary" --base main

# Verify PR
gh pr view <N> --json number,headRefName,baseRefName,state,files,url

# Monitor CI
gh pr checks --watch

# Merge
gh pr merge --squash --delete-branch
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

# Submit review
gh pr review <N> --approve --body "LGTM"
gh pr review <N> --request-changes --body "See inline comments."
```

---

## 4. Issues Management

See `references/github-issues.md` for full details including creating/viewing issues, labels, assignment, commenting, closing/reopening, triage workflows, and bulk operations.

### Quick Reference

| Action | gh | curl |
|--------|-----|------|
| List issues | `gh issue list` | `GET /repos/o/r/issues` |
| Create issue | `gh issue create --title "..." --body "..." --label "bug"` | `POST /repos/o/r/issues` |
| Add labels | `gh issue edit N --add-label "bug"` | `POST /repos/o/r/issues/N/labels` |
| Assign | `gh issue edit N --add-assignee user` | `POST /repos/o/r/issues/N/assignees` |
| Comment | `gh issue comment N --body "..."` | `POST /repos/o/r/issues/N/comments` |
| Close | `gh issue close N` | `PATCH /repos/o/r/issues/N` |

---

## 5. Repository Management

See `references/github-repo-management.md` for full details including cloning, creating repos, forking, branch protection, secrets, releases, GitHub Actions workflows, and gists.

### Quick Reference

| Action | gh | git + curl |
|--------|-----|-----------|
| Clone | `gh repo clone o/r` | `git clone https://github.com/o/r.git` |
| Create repo | `gh repo create name --public` | `curl POST /user/repos` |
| Fork | `gh repo fork o/r --clone` | `curl POST /repos/o/r/forks` + git clone |
| Create release | `gh release create v1.0` | `curl POST /repos/o/r/releases` |
| Set secret | `gh secret set KEY` | `curl PUT /repos/o/r/actions/secrets/KEY` |
| Rerun CI | `gh run rerun ID` | `curl POST /repos/o/r/actions/runs/ID/rerun` |

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
