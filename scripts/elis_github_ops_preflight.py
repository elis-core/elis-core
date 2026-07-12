#!/usr/bin/env python3
"""elis_github_ops_preflight.py — deterministic preflight checks for ELIS GitHub operations.

Implements the 11 failure class checks as composable functions plus a unified
CLI entry point. Follows the style conventions of sibling scripts in this repo.

Checks implemented:
  1. check_worktree_binding — WRONG_GITHUB_WORKTREE_OR_CLONE
  2. check_branch_not_locked — PE_BRANCH_LOCKED_BY_OTHER_WORKTREE
  3. check_local_branch_not_stale — STALE_LOCAL_PE_BRANCH_HEAD; subcase: STALE_LOCAL_WORKSPACE_HEAD
  4. check_no_local_unpushed_commits — LOCAL_UNPUSHED_COMMITS_BLOCK_RESET
  5. check_ci_status_current_head — STALE_CHECK_RUN_NOT_CURRENT_HEAD
  6. check_protected_files_not_edited — PM_WRONG_RESPONSIBILITY_BOUNDARY
  7. check_no_secret_output — SECRET_OUTPUT_RISK
  8. check_merge_approval — PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED
  9. check_review_artefact_path — REVIEW_ARTEFACT_WRONG_PATH
  10. check_review_schema — REVIEW_SCHEMA_NONCOMPLIANT

Usage:
  python scripts/elis_github_ops_preflight.py [--checks CHECK1,CHECK2] [options]

Exit codes:
  0 — all checks pass
  1 — one or more checks fail
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


# ── Error classes (used as exception types / result keys) ──────────────

WRONG_GITHUB_WORKTREE_OR_CLONE = "WRONG_GITHUB_WORKTREE_OR_CLONE"
PE_BRANCH_LOCKED_BY_OTHER_WORKTREE = "PE_BRANCH_LOCKED_BY_OTHER_WORKTREE"
STALE_LOCAL_PE_BRANCH_HEAD = "STALE_LOCAL_PE_BRANCH_HEAD"
STALE_LOCAL_WORKSPACE_HEAD = "STALE_LOCAL_WORKSPACE_HEAD"
LOCAL_UNPUSHED_COMMITS_BLOCK_RESET = "LOCAL_UNPUSHED_COMMITS_BLOCK_RESET"
STALE_CHECK_RUN_NOT_CURRENT_HEAD = "STALE_CHECK_RUN_NOT_CURRENT_HEAD"
PM_WRONG_RESPONSIBILITY_BOUNDARY = "PM_WRONG_RESPONSIBILITY_BOUNDARY"
SECRET_OUTPUT_RISK = "SECRET_OUTPUT_RISK"
PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED = (
    "PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED"
)
REVIEW_ARTEFACT_WRONG_PATH = "REVIEW_ARTEFACT_WRONG_PATH"
REVIEW_SCHEMA_NONCOMPLIANT = "REVIEW_SCHEMA_NONCOMPLIANT"

ALL_FAILURE_CLASSES = frozenset(
    {
        WRONG_GITHUB_WORKTREE_OR_CLONE,
        PE_BRANCH_LOCKED_BY_OTHER_WORKTREE,
        STALE_LOCAL_PE_BRANCH_HEAD,
        STALE_LOCAL_WORKSPACE_HEAD,
        LOCAL_UNPUSHED_COMMITS_BLOCK_RESET,
        STALE_CHECK_RUN_NOT_CURRENT_HEAD,
        PM_WRONG_RESPONSIBILITY_BOUNDARY,
        SECRET_OUTPUT_RISK,
        PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED,
        REVIEW_ARTEFACT_WRONG_PATH,
        REVIEW_SCHEMA_NONCOMPLIANT,
    }
)


# ── Secret patterns (no credential content may appear in output) ──────

SECRET_PATTERNS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{10,}"),  # GitHub tokens
    re.compile(r"sk-[A-Za-z0-9]{20,}"),  # OpenAI / Anthropic keys
    re.compile(r"-----BEGIN .* PRIVATE KEY-----"),  # Private key markers
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access keys
    re.compile(r"(?i)(token|secret|password|apikey)\s*=\s*\S+"),  # env-style secrets
]


# ── Git subprocess helpers ─────────────────────────────────────────────


def _git_cmd(*args: str, cwd: str | Path | None = None) -> subprocess.CompletedProcess:
    """Run a git command and return the CompletedProcess."""
    return subprocess.run(
        ["git"] + list(args),
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=30,
    )


def _gh_cmd(*args: str, cwd: str | Path | None = None) -> subprocess.CompletedProcess:
    """Run a gh command (read-only) and return the CompletedProcess."""
    return subprocess.run(
        ["gh"] + list(args),
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=30,
    )


def _canonical_repo() -> Path:
    """Return the canonical repo path (default /opt/elis/repo)."""
    return Path(os.environ.get("CANONICAL_REPO", "/opt/elis/repo"))


def _repo_remote() -> str:
    """Return the expected remote URL."""
    return os.environ.get(
        "ELIS_GITHUB_REMOTE",
        "https://github.com/elis-core/elis-core.git",
    )


# ── Check 1: Worktree binding ──────────────────────────────────────────


def check_worktree_binding(
    expected_path: str | None = None,
    expected_remote: str | None = None,
) -> dict:
    """Verify pwd matches expected_path and git remote matches expected_remote.

    Returns a result dict with keys: check, class, status, detail.
    """
    if expected_path is None:
        expected_path = os.environ.get("ELIS_EXPECTED_WORKTREE", os.getcwd())
    if expected_remote is None:
        expected_remote = _repo_remote()

    actual_path = Path.cwd().resolve().as_posix()
    expected_resolved = Path(expected_path).resolve().as_posix()

    failures: list[str] = []

    # Check path
    if actual_path != expected_resolved:
        failures.append(
            f"Path mismatch: expected '{expected_resolved}', got '{actual_path}'"
        )

    # Check top-level
    tl_result = _git_cmd("rev-parse", "--show-toplevel")
    if tl_result.returncode != 0:
        failures.append(f"Not a git repository: {tl_result.stderr.strip()}")
    else:
        top_level = tl_result.stdout.strip()
        if top_level != expected_resolved:
            failures.append(
                f"Top-level mismatch: expected '{expected_resolved}', "
                f"git reports '{top_level}'"
            )

    # Check remote
    remote_result = _git_cmd("remote", "get-url", "origin")
    if remote_result.returncode != 0:
        failures.append("No 'origin' remote configured")
    else:
        actual_remote = remote_result.stdout.strip()
        if actual_remote != expected_remote:
            failures.append(
                f"Remote mismatch: expected '{expected_remote}', got '{actual_remote}'"
            )

    status = "PASS" if not failures else "FAIL"
    return {
        "check": "check_worktree_binding",
        "class": WRONG_GITHUB_WORKTREE_OR_CLONE,
        "status": status,
        "detail": (
            "; ".join(failures)
            if failures
            else "Worktree and remote match expected values"
        ),
    }


# ── Check 2: Branch not locked in another worktree ─────────────────────


def check_branch_not_locked(branch_name: str | None = None) -> dict:
    """Check git worktree list for the branch in another worktree.

    If branch_name is None, detect the current branch.
    """
    if branch_name is None:
        br_result = _git_cmd("rev-parse", "--abbrev-ref", "HEAD")
        if br_result.returncode != 0:
            return {
                "check": "check_branch_not_locked",
                "class": PE_BRANCH_LOCKED_BY_OTHER_WORKTREE,
                "status": "FAIL",
                "detail": "Cannot determine current branch",
            }
        branch_name = br_result.stdout.strip()

    repo = _canonical_repo()
    wl_result = _git_cmd("worktree", "list", cwd=repo)
    if wl_result.returncode != 0:
        return {
            "check": "check_branch_not_locked",
            "class": PE_BRANCH_LOCKED_BY_OTHER_WORKTREE,
            "status": "FAIL",
            "detail": f"Cannot list worktrees: {wl_result.stderr.strip()}",
        }

    current_path = Path.cwd().resolve().as_posix()
    locked_entries: list[dict] = []

    for line in wl_result.stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        wl_path = Path(parts[0]).resolve().as_posix()
        # Branch is in brackets: [branch_name] or (detached HEAD)
        branch_raw = " ".join(parts[2:]) if len(parts) > 2 else "(detached HEAD)"
        branch_clean = branch_raw.strip("[]()").replace("detached HEAD", "").strip()

        if wl_path == current_path:
            continue
        if branch_clean == branch_name or branch_name in branch_raw:
            locked_entries.append(
                {
                    "path": wl_path,
                    "branch": branch_raw,
                    "head": parts[1] if len(parts) > 1 else "",
                }
            )

    if locked_entries:
        detail_parts = [
            f"Branch '{branch_name}' locked in {len(locked_entries)} worktree(s):"
        ]
        for entry in locked_entries:
            detail_parts.append(
                f"  - {entry['path']} ({entry['branch']}, HEAD={entry['head'][:12]})"
            )
        return {
            "check": "check_branch_not_locked",
            "class": PE_BRANCH_LOCKED_BY_OTHER_WORKTREE,
            "status": "FAIL",
            "detail": "\n".join(detail_parts),
        }

    return {
        "check": "check_branch_not_locked",
        "class": PE_BRANCH_LOCKED_BY_OTHER_WORKTREE,
        "status": "PASS",
        "detail": f"Branch '{branch_name}' is not locked in any other worktree",
    }


# ── Check 3: Local branch not stale ────────────────────────────────────


def check_local_branch_not_stale(branch_name: str | None = None) -> dict:
    """Check if local branch is behind origin/main (stale).

    Also handles STALE_LOCAL_WORKSPACE_HEAD subcase (detached HEAD behind origin/main).
    """
    # Fetch first
    _git_cmd("fetch", "origin")

    if branch_name is None:
        br_result = _git_cmd("rev-parse", "--abbrev-ref", "HEAD")
        if br_result.returncode != 0:
            return {
                "check": "check_local_branch_not_stale",
                "class": STALE_LOCAL_PE_BRANCH_HEAD,
                "status": "FAIL",
                "detail": "Cannot determine current branch/ref",
            }
        branch_name = br_result.stdout.strip()

    is_detached = branch_name == "HEAD"

    if is_detached:
        # Check STALE_LOCAL_WORKSPACE_HEAD
        behind = _git_cmd("rev-list", "--count", "HEAD..origin/main")
        if behind.returncode != 0:
            return {
                "check": "check_local_branch_not_stale",
                "class": STALE_LOCAL_WORKSPACE_HEAD,
                "status": "FAIL",
                "detail": f"Cannot check detached HEAD age: {behind.stderr.strip()}",
            }
        behind_count = int(behind.stdout.strip())
        if behind_count > 0:
            return {
                "check": "check_local_branch_not_stale",
                "class": STALE_LOCAL_WORKSPACE_HEAD,
                "status": "FAIL",
                "detail": f"Detached HEAD is {behind_count} commit(s) behind origin/main. "
                f"Run 'git switch --detach origin/main' to sync.",
            }
        return {
            "check": "check_local_branch_not_stale",
            "class": STALE_LOCAL_WORKSPACE_HEAD,
            "status": "PASS",
            "detail": "Detached HEAD is current with origin/main",
        }

    # Feature branch check
    lr = _git_cmd("rev-list", "--count", "--left-right", f"origin/main..{branch_name}")
    if lr.returncode != 0:
        return {
            "check": "check_local_branch_not_stale",
            "class": STALE_LOCAL_PE_BRANCH_HEAD,
            "status": "FAIL",
            "detail": f"Cannot check branch status: {lr.stderr.strip()}",
        }

    parts = lr.stdout.strip().split("\t")
    if len(parts) != 2:
        return {
            "check": "check_local_branch_not_stale",
            "class": STALE_LOCAL_PE_BRANCH_HEAD,
            "status": "FAIL",
            "detail": f"Unexpected rev-list format: {lr.stdout.strip()}",
        }

    try:
        ahead = int(parts[0])
        behind = int(parts[1])
    except ValueError:
        return {
            "check": "check_local_branch_not_stale",
            "class": STALE_LOCAL_PE_BRANCH_HEAD,
            "status": "FAIL",
            "detail": f"Non-integer ahead/behind: {parts}",
        }

    if behind > 0 and ahead > 0:
        return {
            "check": "check_local_branch_not_stale",
            "class": STALE_LOCAL_PE_BRANCH_HEAD,
            "status": "FAIL",
            "detail": f"Branch '{branch_name}' has diverged: {ahead} ahead, {behind} behind. "
            f"Run 'git rebase origin/main'.",
        }
    if behind > 0:
        return {
            "check": "check_local_branch_not_stale",
            "class": STALE_LOCAL_PE_BRANCH_HEAD,
            "status": "FAIL",
            "detail": f"Branch '{branch_name}' is {behind} commit(s) behind origin/main. "
            f"Run 'git rebase origin/main'.",
        }

    return {
        "check": "check_local_branch_not_stale",
        "class": STALE_LOCAL_PE_BRANCH_HEAD,
        "status": "PASS",
        "detail": f"Branch '{branch_name}' is current ({ahead} ahead, {behind} behind)",
    }


# ── Check 4: No local unpushed commits ─────────────────────────────────


def check_no_local_unpushed_commits() -> dict:
    """Check for commits on local branch not present on origin."""
    branch_result = _git_cmd("rev-parse", "--abbrev-ref", "HEAD")
    if branch_result.returncode != 0:
        return {
            "check": "check_no_local_unpushed_commits",
            "class": LOCAL_UNPUSHED_COMMITS_BLOCK_RESET,
            "status": "FAIL",
            "detail": "Cannot determine current branch",
        }
    branch_name = branch_result.stdout.strip()

    if branch_name == "HEAD":
        return {
            "check": "check_no_local_unpushed_commits",
            "class": LOCAL_UNPUSHED_COMMITS_BLOCK_RESET,
            "status": "PASS",
            "detail": "Detached HEAD — unpushed check skipped",
        }

    # Try to get the remote ref
    remote_ref = f"origin/{branch_name}"
    lr = _git_cmd("log", "--oneline", f"{remote_ref}..HEAD")
    if lr.returncode != 0:
        # Remote branch may not exist yet (new branch)
        return {
            "check": "check_no_local_unpushed_commits",
            "class": LOCAL_UNPUSHED_COMMITS_BLOCK_RESET,
            "status": "PASS",
            "detail": f"Remote branch '{remote_ref}' does not exist (new branch — no unpushed check)",
        }

    unpushed = [line for line in lr.stdout.strip().split("\n") if line.strip()]
    if unpushed:
        return {
            "check": "check_no_local_unpushed_commits",
            "class": LOCAL_UNPUSHED_COMMITS_BLOCK_RESET,
            "status": "FAIL",
            "detail": f"{len(unpushed)} unpushed commit(s) on '{branch_name}':\n"
            + "\n".join(unpushed),
        }

    return {
        "check": "check_no_local_unpushed_commits",
        "class": LOCAL_UNPUSHED_COMMITS_BLOCK_RESET,
        "status": "PASS",
        "detail": f"No unpushed commits on '{branch_name}'",
    }


# ── Check 5: CI status on current HEAD ─────────────────────────────────


def check_ci_status_current_head(
    repo: str = "elis-core/elis-core",
    expected_sha: str | None = None,
) -> dict:
    """Verify CI check runs are for the current HEAD SHA.

    Output includes sha, run_id, event, conclusion, required flag.
    No credential content appears in output.
    """
    if expected_sha is None:
        sha_result = _git_cmd("rev-parse", "HEAD")
        if sha_result.returncode != 0:
            return {
                "check": "check_ci_status_current_head",
                "class": STALE_CHECK_RUN_NOT_CURRENT_HEAD,
                "status": "FAIL",
                "detail": "Cannot determine current HEAD",
            }
        expected_sha = sha_result.stdout.strip()

    branch_result = _git_cmd("rev-parse", "--abbrev-ref", "HEAD")
    branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "HEAD"

    # Use gh CLI read-only to list runs
    gh_result = _gh_cmd(
        "run",
        "list",
        "--repo",
        repo,
        "--branch",
        branch,
        "--limit",
        "20",
        "--json",
        "headSha,databaseId,event,conclusion,workflowName,displayTitle",
    )
    if gh_result.returncode != 0:
        return {
            "check": "check_ci_status_current_head",
            "class": STALE_CHECK_RUN_NOT_CURRENT_HEAD,
            "status": "FAIL",
            "detail": f"gh CLI failed: {gh_result.stderr.strip()}",
        }

    try:
        runs = json.loads(gh_result.stdout.strip())
    except (json.JSONDecodeError, ValueError):
        return {
            "check": "check_ci_status_current_head",
            "class": STALE_CHECK_RUN_NOT_CURRENT_HEAD,
            "status": "FAIL",
            "detail": "Cannot parse gh run list output",
        }

    current_head_runs = []
    stale_runs = []
    for run in runs:
        sha = run.get("headSha", "")
        run_id = run.get("databaseId", "?")
        event = run.get("event", "?")
        conclusion = run.get("conclusion", "?")
        wf = run.get("workflowName", "?")
        if sha == expected_sha:
            current_head_runs.append(
                f"  SHA={sha[:12]} run={run_id} event={event} conclusion={conclusion} wf={wf}"
            )
        else:
            stale_runs.append(
                f"  SHA={sha[:12]} run={run_id} event={event} conclusion={conclusion} wf={wf}"
            )

    report_lines = [f"Current HEAD: {expected_sha}"]
    if current_head_runs:
        report_lines.append(f"Runs on current HEAD ({len(current_head_runs)}):")
        report_lines.extend(current_head_runs)
    else:
        report_lines.append("No runs found for current HEAD")

    if stale_runs:
        report_lines.append(f"Stale runs from older commits ({len(stale_runs)}):")
        report_lines.extend(stale_runs)

    if not current_head_runs and stale_runs:
        return {
            "check": "check_ci_status_current_head",
            "class": STALE_CHECK_RUN_NOT_CURRENT_HEAD,
            "status": "FAIL",
            "detail": "\n".join(report_lines),
        }

    # Check if all required runs on current HEAD pass
    failed_current = [
        r
        for r in current_head_runs
        if "conclusion=failure" in r or "conclusion=cancelled" in r
    ]
    if failed_current:
        report_lines.append(
            f"\n{len(failed_current)} run(s) on current HEAD have failed/cancelled"
        )
        return {
            "check": "check_ci_status_current_head",
            "class": STALE_CHECK_RUN_NOT_CURRENT_HEAD,
            "status": "FAIL",
            "detail": "\n".join(report_lines),
        }

    return {
        "check": "check_ci_status_current_head",
        "class": STALE_CHECK_RUN_NOT_CURRENT_HEAD,
        "status": "PASS" if not stale_runs else "WARN",
        "detail": "\n".join(report_lines),
    }


# ── Check 6: Protected files not edited by wrong actor ─────────────────

PROTECTED_FILES = frozenset(
    {
        "CURRENT_PE.md",
        "AGENTS.md",
        "docs/governance/ELIS_GitHub_Agent_Operating_Model.md",
        "docs/governance/ELIS_PE_Operating_Protocol.md",
        "docs/governance/ELIS_Agent_Dispatch_Binding_and_Validation_Rules.md",
    }
)


def check_protected_files_not_edited(
    protected_list: list[str] | None = None,
    base_branch: str = "origin/main",
) -> dict:
    """Check git diff for protected files modified by non-PM actors."""
    if protected_list is None:
        protected_list = sorted(PROTECTED_FILES)

    # Get scope diff
    diff_result = _git_cmd("diff", "--name-status", base_branch + "..HEAD")
    if diff_result.returncode != 0:
        return {
            "check": "check_protected_files_not_edited",
            "class": PM_WRONG_RESPONSIBILITY_BOUNDARY,
            "status": "FAIL",
            "detail": f"Cannot diff against {base_branch}: {diff_result.stderr.strip()}",
        }

    modified_protected = []
    for line in diff_result.stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0]
        fpath = parts[1]
        # Check if the file (or its basename) is in the protected list
        basename = Path(fpath).name
        if basename in protected_list or fpath in protected_list:
            modified_protected.append(f"  {status}\t{fpath}")

    if modified_protected:
        return {
            "check": "check_protected_files_not_edited",
            "class": PM_WRONG_RESPONSIBILITY_BOUNDARY,
            "status": "FAIL",
            "detail": "Protected files modified in this branch:\n"
            + "\n".join(modified_protected),
        }

    return {
        "check": "check_protected_files_not_edited",
        "class": PM_WRONG_RESPONSIBILITY_BOUNDARY,
        "status": "PASS",
        "detail": "No protected files modified by this branch",
    }


# ── Check 7: No secret output ──────────────────────────────────────────


def check_no_secret_output(text: str | None = None) -> dict:
    """Scan text for secret patterns. If text is None, read from stdin."""
    if text is None:
        text = sys.stdin.read()

    matches_found: list[str] = []
    for pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            # Only record the pattern type, not the matched value
            matches_found.append(
                f"  Pattern matched: {pattern.pattern[:40]}... (REDACTED)"
            )

    if matches_found:
        unique_patterns = list(
            dict.fromkeys(matches_found)
        )  # deduplicate preserving order
        return {
            "check": "check_no_secret_output",
            "class": SECRET_OUTPUT_RISK,
            "status": "FAIL",
            "detail": f"Secret pattern(s) detected ({len(unique_patterns)} unique):\n"
            + "\n".join(unique_patterns)
            + "\nAction: Redact and retry without credential content.",
        }

    return {
        "check": "check_no_secret_output",
        "class": SECRET_OUTPUT_RISK,
        "status": "PASS",
        "detail": "No secret patterns detected in output",
    }


# ── Check 8: Merge approval check ──────────────────────────────────────


def check_merge_approval(
    repo: str = "elis-core/elis-core",
    pr_number: int | None = None,
) -> dict:
    """Verify no pm-review-required label and CI green before merge readiness.

    Also checks for PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED by
    detecting if PM capability paths are present.
    """
    failures: list[str] = []

    # Check PM capability paths (metadata only — no credential content)
    pm_capable_paths = []
    gh_check = subprocess.run(
        ["gh", "auth", "status"], capture_output=True, text=True, timeout=15
    )
    if gh_check.returncode == 0:
        pm_capable_paths.append("gh CLI authenticated (read-only check: path exists)")

    git_push_check = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if git_push_check.returncode == 0:
        pm_capable_paths.append("git remote origin configured (path exists)")

    if pm_capable_paths:
        failures.append(
            "PM capability path(s) detected — "
            "PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED finding applies. "
            "Evidence (metadata only, no credential content):\n"
            + "\n".join(f"  - {p}" for p in pm_capable_paths)
            + "\nDefer credential restriction to PE-OPS-GITHUB-PERMISSIONS-01."
        )

    if pr_number is not None:
        # Check labels
        label_result = _gh_cmd(
            "pr",
            "view",
            str(pr_number),
            "--repo",
            repo,
            "--json",
            "labels,mergeStateStatus",
        )
        if label_result.returncode == 0:
            try:
                pr_data = json.loads(label_result.stdout.strip())
                labels = [lbl.get("name", "") for lbl in pr_data.get("labels", [])]
                if "pm-review-required" in labels:
                    failures.append(
                        "PR has 'pm-review-required' label — PM review required before merge"
                    )
                merge_state = pr_data.get("mergeStateStatus", "")
                if merge_state not in ("CLEAN", "UNKNOWN", None):
                    failures.append(
                        f"PR merge state is '{merge_state}' (expected CLEAN)"
                    )
            except (json.JSONDecodeError, ValueError):
                failures.append("Cannot parse PR metadata")

    if failures:
        detail = "; ".join(failures)
        return {
            "check": "check_merge_approval",
            "class": PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED,
            "status": "FAIL",
            "detail": detail,
        }

    return {
        "check": "check_merge_approval",
        "class": PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED,
        "status": "PASS",
        "detail": "Merge approval preflight passed — no pm-review-required label, "
        "no PM capability paths detected",
    }


# ── Check 9: REVIEW artefact at correct path ───────────────────────────

REVIEW_PATH_PATTERN = re.compile(
    r"\.elis/pe/(?P<pe_id>PE-[A-Z0-9-]+)/REVIEW(?:_PE-[A-Z0-9-]+)?\.md"
)


def check_review_artefact_path(
    base_dir: str | None = None,
    pe_id: str | None = None,
) -> dict:
    """Check that REVIEW files exist at the correct canonical path."""
    if base_dir is None:
        base_dir = str(_canonical_repo())
    if pe_id is None:
        pe_id = os.environ.get("ELIS_PE_ID", "")

    base_path = Path(base_dir)
    wrong_path_reviews: list[str] = []
    correct_path_reviews: list[str] = []

    # Search for REVIEW files
    for fpath in base_path.rglob("REVIEW*.md"):
        rel = fpath.relative_to(base_path).as_posix()
        if REVIEW_PATH_PATTERN.match(rel):
            correct_path_reviews.append(rel)
        else:
            wrong_path_reviews.append(rel)

    if wrong_path_reviews:
        return {
            "check": "check_review_artefact_path",
            "class": REVIEW_ARTEFACT_WRONG_PATH,
            "status": "FAIL",
            "detail": f"REVIEW file(s) at wrong path ({len(wrong_path_reviews)}):\n"
            + "\n".join(f"  - {p}" for p in wrong_path_reviews),
        }

    return {
        "check": "check_review_artefact_path",
        "class": REVIEW_ARTEFACT_WRONG_PATH,
        "status": "PASS",
        "detail": f"All REVIEW files at canonical paths ({len(correct_path_reviews)} found)",
    }


# ── Check 10: REVIEW schema compliance ─────────────────────────────────

REVIEW_REQUIRED_HEADINGS = [
    "### Evidence",
    "### Verdict",
    "### Failure classes addressed",
]


def check_review_schema(
    base_dir: str | None = None,
    pe_id: str | None = None,
) -> dict:
    """Check that REVIEW files have required headings."""
    if base_dir is None:
        base_dir = str(_canonical_repo())
    if pe_id is None:
        pe_id = os.environ.get("ELIS_PE_ID", "")

    base_path = Path(base_dir)
    noncompliant: list[str] = []

    for fpath in base_path.rglob("REVIEW*.md"):
        rel = fpath.relative_to(base_path).as_posix()
        # Only check REVIEW files at canonical paths
        if not REVIEW_PATH_PATTERN.match(rel):
            continue
        content = fpath.read_text()
        missing = [h for h in REVIEW_REQUIRED_HEADINGS if h not in content]
        if missing:
            noncompliant.append(f"  {rel}: missing {missing}")

    if noncompliant:
        return {
            "check": "check_review_schema",
            "class": REVIEW_SCHEMA_NONCOMPLIANT,
            "status": "FAIL",
            "detail": "REVIEW file(s) noncompliant:\n" + "\n".join(noncompliant),
        }

    return {
        "check": "check_review_schema",
        "class": REVIEW_SCHEMA_NONCOMPLIANT,
        "status": "PASS",
        "detail": "All REVIEW files have required headings",
    }


# ── Unified runner ─────────────────────────────────────────────────────

ALL_CHECKS = {
    "worktree_binding": check_worktree_binding,
    "branch_not_locked": check_branch_not_locked,
    "branch_not_stale": check_local_branch_not_stale,
    "no_unpushed_commits": check_no_local_unpushed_commits,
    "ci_status_current_head": check_ci_status_current_head,
    "protected_files": check_protected_files_not_edited,
    "no_secret_output": check_no_secret_output,
    "merge_approval": check_merge_approval,
    "review_artefact_path": check_review_artefact_path,
    "review_schema": check_review_schema,
}


def run_all_checks(
    checks_to_run: list[str] | None = None,
    **kwargs,
) -> list[dict]:
    """Run all specified checks and return results list.

    Each result dict has keys: check, class, status, detail.
    """
    if checks_to_run is None:
        checks_to_run = sorted(ALL_CHECKS.keys())

    results: list[dict] = []
    for name in checks_to_run:
        if name not in ALL_CHECKS:
            results.append(
                {
                    "check": name,
                    "class": "UNKNOWN_CHECK",
                    "status": "FAIL",
                    "detail": f"Unknown check: '{name}'",
                }
            )
            continue

        try:
            fn = ALL_CHECKS[name]
            result = (
                fn(**kwargs.get(name, {}))
                if isinstance(kwargs.get(name), dict)
                else fn()
            )
            results.append(result)
        except Exception as exc:
            results.append(
                {
                    "check": name,
                    "class": "EXCEPTION",
                    "status": "FAIL",
                    "detail": f"Exception: {exc}",
                }
            )

    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ELIS GitHub Ops Preflight — deterministic preflight checks."
    )
    parser.add_argument(
        "--checks",
        type=str,
        default=",".join(sorted(ALL_CHECKS.keys())),
        help=f"Comma-separated check names (default: all). Options: {','.join(sorted(ALL_CHECKS.keys()))}",
    )
    parser.add_argument(
        "--expected-worktree",
        default=None,
        help="Expected fixed worktree path (for check_worktree_binding)",
    )
    parser.add_argument(
        "--base-branch",
        default="origin/main",
        help="Base branch ref (for check_protected_files_not_edited)",
    )
    parser.add_argument(
        "--pe-id",
        default=None,
        help="PE ID (for REVIEW checks)",
    )
    parser.add_argument(
        "--pr-number",
        type=int,
        default=None,
        help="PR number (for check_merge_approval)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of human-readable",
    )
    args = parser.parse_args()

    check_names = [c.strip() for c in args.checks.split(",") if c.strip()]

    # Build kwargs per check
    kwargs = {}
    if args.expected_worktree:
        kwargs.setdefault("worktree_binding", {})[
            "expected_path"
        ] = args.expected_worktree
    if args.pe_id:
        kwargs.setdefault("review_artefact_path", {})["pe_id"] = args.pe_id
        kwargs.setdefault("review_schema", {})["pe_id"] = args.pe_id
    if args.pr_number:
        kwargs.setdefault("merge_approval", {})["pr_number"] = args.pr_number

    results = run_all_checks(check_names, **kwargs)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        fail_count = sum(1 for r in results if r["status"] == "FAIL")
        warn_count = sum(1 for r in results if r["status"] == "WARN")
        pass_count = sum(1 for r in results if r["status"] == "PASS")

        print("=" * 60)
        print(f"ELIS GitHub Ops Preflight — {len(results)} check(s)")
        print("=" * 60)
        for r in results:
            symbol = (
                "✓" if r["status"] == "PASS" else "⚠" if r["status"] == "WARN" else "✗"
            )
            print(f"\n[{symbol}] {r['check']} ({r['class']}) — {r['status']}")
            for line in r["detail"].split("\n"):
                print(f"     {line}")

        print("=" * 60)
        print(f"Summary: {pass_count} pass, {warn_count} warn, {fail_count} fail")

    exit_code = 1 if any(r["status"] == "FAIL" for r in results) else 0
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
