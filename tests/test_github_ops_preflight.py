#!/usr/bin/env python3
"""Tests for scripts/elis_github_ops_preflight.py.

Covers all 11 failure classes plus edge cases.
Uses pytest. Mocks git/gh subprocess calls for deterministic testing.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch


SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts" / "elis_github_ops_preflight.py"
)


def _load():
    """Import the module fresh."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("elis_github_ops_preflight", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# We load the module once and access it through fixtures.
# Use a fixture to reload when we want to patch internals.

MODULE = _load()


# ── Helpers ─────────────────────────────────────────────────────────────


def _make_completed(returncode=0, stdout="", stderr=""):
    """Create a subprocess.CompletedProcess-like mock."""
    cp = MagicMock(spec=subprocess.CompletedProcess)
    cp.returncode = returncode
    cp.stdout = stdout
    cp.stderr = stderr
    return cp


# ── Test 1: check_worktree_binding → WRONG_GITHUB_WORKTREE_OR_CLONE ────


class TestCheckWorktreeBinding:
    """Check 1 — WRONG_GITHUB_WORKTREE_OR_CLONE."""

    def test_pass_matches_path_and_remote(self, monkeypatch, tmp_path):
        """When pwd and remote match, should PASS."""
        test_path = str(tmp_path)
        test_remote = "https://github.com/elis-core/elis-core.git"

        monkeypatch.chdir(tmp_path)

        with patch.object(MODULE, "_git_cmd") as mock_git:
            # rev-parse --show-toplevel
            mock_git.side_effect = [
                _make_completed(stdout=test_path),  # show-toplevel
                _make_completed(stdout=test_remote),  # remote get-url origin
            ]
            result = MODULE.check_worktree_binding(
                expected_path=test_path, expected_remote=test_remote
            )

        assert result["status"] == "PASS"
        assert result["class"] == MODULE.WRONG_GITHUB_WORKTREE_OR_CLONE

    def test_fail_wrong_path(self, monkeypatch):
        """When pwd does not match expected path, should FAIL."""
        wrong_path = "/opt/elis/agent-worktrees/wrong-path"
        expected_path = "/opt/elis/agent-worktrees/github-agent"

        # Mock Path.cwd().resolve() to return the wrong path
        with patch.object(MODULE.Path, "cwd") as mock_cwd:
            mock_cwd.return_value = MagicMock()
            mock_cwd.return_value.resolve.return_value = Path(wrong_path)

            with patch.object(MODULE, "_git_cmd") as mock_git:
                mock_git.side_effect = [
                    _make_completed(returncode=0, stdout=wrong_path),
                    _make_completed(
                        returncode=0,
                        stdout="https://github.com/elis-core/elis-core.git",
                    ),
                ]
                result = MODULE.check_worktree_binding(
                    expected_path=expected_path,
                    expected_remote="https://github.com/elis-core/elis-core.git",
                )

        assert result["status"] == "FAIL"
        assert result["class"] == MODULE.WRONG_GITHUB_WORKTREE_OR_CLONE

    def test_fail_wrong_remote(self, monkeypatch, tmp_path):
        """When remote does not match expected, should FAIL."""
        test_path = str(tmp_path)
        monkeypatch.chdir(tmp_path)
        with patch.object(MODULE, "_git_cmd") as mock_git:
            mock_git.side_effect = [
                _make_completed(stdout=test_path),
                _make_completed(stdout="https://wrong-remote.com/repo.git"),
            ]
            result = MODULE.check_worktree_binding(
                expected_path=test_path,
                expected_remote="https://github.com/elis-core/elis-core.git",
            )

        assert result["status"] == "FAIL"
        assert "Remote mismatch" in result["detail"]


# ── Test 2: check_branch_not_locked → PE_BRANCH_LOCKED_BY_OTHER_WORKTREE ─


class TestCheckBranchNotLocked:
    """Check 2 — PE_BRANCH_LOCKED_BY_OTHER_WORKTREE."""

    def test_pass_branch_not_locked(self, monkeypatch, tmp_path):
        """When branch is not found in any other worktree, should PASS."""
        monkeypatch.chdir(tmp_path)
        current = str(tmp_path)
        with patch.object(MODULE, "_git_cmd") as mock_git:
            mock_git.side_effect = [
                _make_completed(stdout="feature/pe-test"),
                _make_completed(
                    stdout=(
                        f"{current}  d78fc5db [feature/pe-test]\n"
                        "/opt/elis/agent-worktrees/github-agent  43f1c22 [main]\n"
                    )
                ),
            ]
            result = MODULE.check_branch_not_locked("feature/pe-test")
        assert result["status"] == "PASS"

    def test_fail_branch_locked_in_other_worktree(self, monkeypatch, tmp_path):
        """When branch exists in another worktree, should FAIL."""
        monkeypatch.chdir(tmp_path)
        current = str(tmp_path)
        with patch.object(MODULE, "_git_cmd") as mock_git:
            mock_git.return_value = _make_completed(
                stdout=(
                    f"{current}  d78fc5db [main]\n"
                    "/opt/elis/agent-worktrees/infra-val-a  3d27684 [feature/pe-locked]\n"
                )
            )
            result = MODULE.check_branch_not_locked("feature/pe-locked")
        assert result["status"] == "FAIL"
        assert result["class"] == MODULE.PE_BRANCH_LOCKED_BY_OTHER_WORKTREE
        assert "locked" in result["detail"].lower()

    def test_pass_own_worktree_not_counted(self, monkeypatch, tmp_path):
        """When branch is in current worktree, should not count as locked."""
        monkeypatch.chdir(tmp_path)
        current = str(tmp_path)
        with patch.object(MODULE, "_git_cmd") as mock_git:
            mock_git.side_effect = [
                _make_completed(stdout="feature/pe-test"),
                _make_completed(
                    stdout=(
                        f"{current}  d78fc5db [feature/pe-test]\n"
                        "/opt/elis/agent-worktrees/github-agent  43f1c22 [main]\n"
                    )
                ),
            ]
            result = MODULE.check_branch_not_locked("feature/pe-test")
        assert result["status"] == "PASS"


# ── Test 3: check_local_branch_not_stale → STALE_LOCAL_PE_BRANCH_HEAD ──


class TestCheckLocalBranchNotStale:
    """Check 3 — STALE_LOCAL_PE_BRANCH_HEAD + STALE_LOCAL_WORKSPACE_HEAD."""

    def test_pass_current_branch(self, monkeypatch):
        """When branch is current with origin/main, should PASS."""
        with patch.object(MODULE, "_git_cmd") as mock_git:
            mock_git.side_effect = [
                _make_completed(),  # git fetch origin
                _make_completed(stdout="3\t0"),  # rev-list --count --left-right
            ]
            result = MODULE.check_local_branch_not_stale("feature/pe-test")
        assert result["status"] == "PASS"

    def test_fail_behind_origin(self, monkeypatch):
        """When branch is behind origin/main, should FAIL."""
        with patch.object(MODULE, "_git_cmd") as mock_git:
            mock_git.side_effect = [
                _make_completed(),  # git fetch origin
                _make_completed(stdout="feature/pe-test"),
                _make_completed(stdout="0\t5"),  # 0 ahead, 5 behind
            ]
            result = MODULE.check_local_branch_not_stale("feature/pe-test")
        assert result["status"] == "FAIL"
        assert result["class"] == MODULE.STALE_LOCAL_PE_BRANCH_HEAD

    def test_fail_diverged(self, monkeypatch):
        """When branch is both ahead and behind, should FAIL."""
        with patch.object(MODULE, "_git_cmd") as mock_git:
            mock_git.side_effect = [
                _make_completed(),  # git fetch origin
                _make_completed(stdout="2\t3"),  # 2 ahead, 3 behind
            ]
            result = MODULE.check_local_branch_not_stale("feature/pe-test")
        assert result["status"] == "FAIL"
        assert "diverged" in result["detail"].lower()

    def test_fail_stale_detached_head(self, monkeypatch):
        """When detached HEAD is behind origin/main, should FAIL with STALE_LOCAL_WORKSPACE_HEAD."""
        with patch.object(MODULE, "_git_cmd") as mock_git:
            mock_git.side_effect = [
                _make_completed(),  # git fetch origin
                _make_completed(stdout="HEAD"),  # detached HEAD
                _make_completed(stdout="10"),  # 10 behind
            ]
            result = MODULE.check_local_branch_not_stale()
        assert result["status"] == "FAIL"
        assert result["class"] == MODULE.STALE_LOCAL_WORKSPACE_HEAD

    def test_pass_current_detached_head(self, monkeypatch):
        """When detached HEAD is current, should PASS."""
        with patch.object(MODULE, "_git_cmd") as mock_git:
            mock_git.side_effect = [
                _make_completed(),  # git fetch origin
                _make_completed(stdout="HEAD"),
                _make_completed(stdout="0"),  # 0 behind
            ]
            result = MODULE.check_local_branch_not_stale()
        assert result["status"] == "PASS"


# ── Test 4: check_no_local_unpushed_commits → LOCAL_UNPUSHED_COMMITS_BLOCK_RESET ──


class TestCheckNoLocalUnpushedCommits:
    """Check 4 — LOCAL_UNPUSHED_COMMITS_BLOCK_RESET."""

    def test_pass_no_unpushed(self, monkeypatch):
        """When no unpushed commits, should PASS."""
        with patch.object(MODULE, "_git_cmd") as mock_git:
            mock_git.side_effect = [
                _make_completed(stdout="feature/pe-test"),
                _make_completed(stdout=""),  # log empty — no unpushed
            ]
            result = MODULE.check_no_local_unpushed_commits()
        assert result["status"] == "PASS"

    def test_fail_has_unpushed(self, monkeypatch):
        """When unpushed commits exist, should FAIL."""
        with patch.object(MODULE, "_git_cmd") as mock_git:
            mock_git.side_effect = [
                _make_completed(stdout="feature/pe-test"),
                _make_completed(
                    stdout=("abc1234 First commit\n" "def5678 Second commit\n")
                ),
            ]
            result = MODULE.check_no_local_unpushed_commits()
        assert result["status"] == "FAIL"
        assert result["class"] == MODULE.LOCAL_UNPUSHED_COMMITS_BLOCK_RESET

    def test_pass_remote_branch_does_not_exist(self, monkeypatch):
        """When remote branch does not exist yet, should PASS."""
        with patch.object(MODULE, "_git_cmd") as mock_git:
            mock_git.side_effect = [
                _make_completed(stdout="feature/pe-new"),
                _make_completed(returncode=128, stderr="fatal: ambiguous argument"),
            ]
            result = MODULE.check_no_local_unpushed_commits()
        assert result["status"] == "PASS"

    def test_pass_detached_head(self, monkeypatch):
        """When in detached HEAD state, should PASS."""
        with patch.object(MODULE, "_git_cmd") as mock_git:
            mock_git.side_effect = [
                _make_completed(stdout="HEAD"),
            ]
            result = MODULE.check_no_local_unpushed_commits()
        assert result["status"] == "PASS"


# ── Test 5: check_ci_status_current_head → STALE_CHECK_RUN_NOT_CURRENT_HEAD ──


class TestCheckCiStatusCurrentHead:
    """Check 5 — STALE_CHECK_RUN_NOT_CURRENT_HEAD."""

    def test_pass_current_head_has_green_runs(self, monkeypatch):
        """When CI runs exist for current HEAD and all pass, should PASS."""
        head_sha = "abc1234def5678abc1234def5678abc1234def56"
        with patch.object(MODULE, "_git_cmd") as mock_git:
            mock_git.side_effect = [
                _make_completed(stdout=head_sha),  # rev-parse HEAD
                _make_completed(
                    stdout="feature/pe-test"
                ),  # rev-parse --abbrev-ref HEAD
            ]
        with patch.object(MODULE, "_gh_cmd") as mock_gh:
            mock_gh.return_value = _make_completed(
                stdout=json.dumps(
                    [
                        {
                            "headSha": head_sha,
                            "databaseId": 1001,
                            "event": "push",
                            "conclusion": "success",
                            "workflowName": "CI",
                            "displayTitle": "CI run",
                        },
                    ]
                )
            )
            result = MODULE.check_ci_status_current_head(expected_sha=head_sha)
        assert result["status"] == "PASS"

    def test_fail_stale_runs_only(self, monkeypatch):
        """When CI runs exist for old SHAs only, should FAIL."""
        head_sha = "abc1234def5678abc1234def5678abc1234def56"
        with patch.object(MODULE, "_git_cmd") as mock_git:
            mock_git.side_effect = [
                _make_completed(stdout=head_sha),
                _make_completed(stdout="feature/pe-test"),
            ]
        with patch.object(MODULE, "_gh_cmd") as mock_gh:
            mock_gh.return_value = _make_completed(
                stdout=json.dumps(
                    [
                        {
                            "headSha": "oldsha00000000000000000000000000000000000",
                            "databaseId": 999,
                            "event": "push",
                            "conclusion": "success",
                            "workflowName": "CI",
                            "displayTitle": "Old run",
                        },
                    ]
                )
            )
            result = MODULE.check_ci_status_current_head(expected_sha=head_sha)
        assert result["status"] == "FAIL"
        assert result["class"] == MODULE.STALE_CHECK_RUN_NOT_CURRENT_HEAD

    def test_warn_current_with_stale(self, monkeypatch):
        """When current HEAD has runs but stale ones also exist, should WARN."""
        head_sha = "abc1234def5678abc1234def5678abc1234def56"
        with patch.object(MODULE, "_git_cmd") as mock_git:
            mock_git.side_effect = [
                _make_completed(stdout=head_sha),
                _make_completed(stdout="feature/pe-test"),
            ]
        with patch.object(MODULE, "_gh_cmd") as mock_gh:
            mock_gh.return_value = _make_completed(
                stdout=json.dumps(
                    [
                        {
                            "headSha": head_sha,
                            "databaseId": 1001,
                            "event": "push",
                            "conclusion": "success",
                            "workflowName": "CI",
                        },
                        {
                            "headSha": "oldsha00000000000000000000000000000000000",
                            "databaseId": 999,
                            "event": "push",
                            "conclusion": "success",
                            "workflowName": "Old CI",
                        },
                    ]
                )
            )
            result = MODULE.check_ci_status_current_head(expected_sha=head_sha)
        assert result["status"] == "WARN"


# ── Test 6: check_protected_files_not_edited → PM_WRONG_RESPONSIBILITY_BOUNDARY ──


class TestCheckProtectedFilesNotEdited:
    """Check 6 — PM_WRONG_RESPONSIBILITY_BOUNDARY."""

    def test_pass_no_protected_files(self, monkeypatch):
        """When no protected files in diff, should PASS."""
        with patch.object(MODULE, "_git_cmd") as mock_git:
            mock_git.return_value = _make_completed(
                stdout=(
                    "M\tscripts/elis_github_ops_preflight.py\n"
                    "A\ttests/test_github_ops_preflight.py\n"
                )
            )
            result = MODULE.check_protected_files_not_edited()
        assert result["status"] == "PASS"

    def test_fail_protected_file_modified(self, monkeypatch):
        """When a protected file is in diff, should FAIL."""
        with patch.object(MODULE, "_git_cmd") as mock_git:
            mock_git.return_value = _make_completed(
                stdout=("M\tCURRENT_PE.md\n" "M\tscripts/some_code.py\n")
            )
            result = MODULE.check_protected_files_not_edited()
        assert result["status"] == "FAIL"
        assert result["class"] == MODULE.PM_WRONG_RESPONSIBILITY_BOUNDARY
        assert "CURRENT_PE.md" in result["detail"]

    def test_fail_protected_file_in_subdir(self, monkeypatch):
        """When protected file with subdir path is in diff, should FAIL."""
        with patch.object(MODULE, "_git_cmd") as mock_git:
            mock_git.return_value = _make_completed(
                stdout=("M\tdocs/governance/ELIS_GitHub_Agent_Operating_Model.md\n")
            )
            result = MODULE.check_protected_files_not_edited(
                protected_list=["ELIS_GitHub_Agent_Operating_Model.md"]
            )
        assert result["status"] == "FAIL"
        assert result["class"] == MODULE.PM_WRONG_RESPONSIBILITY_BOUNDARY


# ── Test 7: check_no_secret_output → SECRET_OUTPUT_RISK ────────────────


class TestCheckNoSecretOutput:
    """Check 7 — SECRET_OUTPUT_RISK."""

    def test_pass_clean_text(self):
        """When no secret patterns in text, should PASS."""
        result = MODULE.check_no_secret_output(
            "This is a normal log message\nNo secrets here\n"
        )
        assert result["status"] == "PASS"

    def test_fail_github_token(self):
        """When text contains a GitHub token, should FAIL."""
        # Use a clearly fake token for testing
        text = "Output contains ghp_abc123def456ghi789jkl012mno345pqr678"
        result = MODULE.check_no_secret_output(text)
        assert result["status"] == "FAIL"
        assert result["class"] == MODULE.SECRET_OUTPUT_RISK

    def test_fail_private_key_marker(self):
        """When text contains a private key marker, should FAIL."""
        text = (
            "-----BEGIN RSA PRIVATE KEY-----\nbase64data\n-----END RSA PRIVATE KEY-----"
        )
        result = MODULE.check_no_secret_output(text)
        assert result["status"] == "FAIL"
        assert result["class"] == MODULE.SECRET_OUTPUT_RISK

    def test_fail_env_style_secret(self):
        """When text contains env-style GITHUB_TOKEN=..., should FAIL."""
        text = "export GITHUB_TOKEN=ghp_abc123def456\n"
        result = MODULE.check_no_secret_output(text)
        assert result["status"] == "FAIL"
        assert result["class"] == MODULE.SECRET_OUTPUT_RISK


# ── Test 8: check_merge_approval → PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED ──


class TestCheckMergeApproval:
    """Check 8 — PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED."""

    def test_pass_no_pm_capability_detected(self, monkeypatch):
        """When no PM capability paths are detected, should PASS."""
        with patch.object(subprocess, "run") as mock_run:
            mock_run.side_effect = [
                _make_completed(returncode=1, stderr="not logged in"),  # gh auth
                _make_completed(returncode=128, stderr="not a git repo"),  # git remote
            ]
            result = MODULE.check_merge_approval()
        assert result["status"] == "PASS"

    def test_fail_pm_capability_detected(self, monkeypatch):
        """When PM gh auth is detected, should FAIL."""
        with patch.object(subprocess, "run") as mock_run:
            mock_run.side_effect = [
                _make_completed(
                    stdout="Logged in to github.com as rochasamurai"
                ),  # gh auth
                _make_completed(returncode=128, stderr="not a git repo"),
            ]
            result = MODULE.check_merge_approval()
        assert result["status"] == "FAIL"
        assert result["class"] == MODULE.PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED
        assert "PM capability path" in result["detail"]

    def test_fail_pm_review_label(self, monkeypatch):
        """When PR has pm-review-required label, should FAIL."""
        with patch.object(subprocess, "run") as mock_run:
            # First two calls are for gh auth and git remote
            mock_run.side_effect = [
                _make_completed(returncode=1, stderr="not logged in"),
                _make_completed(returncode=128, stderr="not a git repo"),
            ]
        with patch.object(MODULE, "_gh_cmd") as mock_gh:
            mock_gh.return_value = _make_completed(
                stdout=json.dumps(
                    {
                        "labels": [{"name": "pm-review-required"}],
                        "mergeStateStatus": "CLEAN",
                    }
                )
            )
            result = MODULE.check_merge_approval(pr_number=42)
        assert result["status"] == "FAIL"


# ── Test 9: check_review_artefact_path → REVIEW_ARTEFACT_WRONG_PATH ────


class TestCheckReviewArtefactPath:
    """Check 9 — REVIEW_ARTEFACT_WRONG_PATH."""

    def test_pass_correct_path(self, tmp_path):
        """When REVIEW file is at canonical path, should PASS."""
        pe_dir = tmp_path / ".elis" / "pe" / "PE-OPS-GITHUB-SKILLS-01"
        pe_dir.mkdir(parents=True)
        review = pe_dir / "REVIEW_PE-OPS-GITHUB-SKILLS-01.md"
        review.write_text("# Test REVIEW")
        result = MODULE.check_review_artefact_path(base_dir=str(tmp_path))
        assert result["status"] == "PASS"

    def test_fail_wrong_path(self, tmp_path):
        """When REVIEW file is at wrong path, should FAIL."""
        wrong = tmp_path / "docs" / "REVIEW_PE-OPS-GITHUB-SKILLS-01.md"
        wrong.parent.mkdir(parents=True)
        wrong.write_text("# Test REVIEW at wrong path")
        result = MODULE.check_review_artefact_path(base_dir=str(tmp_path))
        assert result["status"] == "FAIL"
        assert result["class"] == MODULE.REVIEW_ARTEFACT_WRONG_PATH

    def test_pass_no_review_files(self, tmp_path):
        """When no REVIEW files exist, should PASS."""
        result = MODULE.check_review_artefact_path(base_dir=str(tmp_path))
        assert result["status"] == "PASS"


# ── Test 10: check_review_schema → REVIEW_SCHEMA_NONCOMPLIANT ──────────


class TestCheckReviewSchema:
    """Check 10 — REVIEW_SCHEMA_NONCOMPLIANT."""

    def test_pass_all_required_headings(self, tmp_path):
        """When REVIEW file has all required headings, should PASS."""
        pe_dir = tmp_path / ".elis" / "pe" / "PE-OPS-GITHUB-SKILLS-01"
        pe_dir.mkdir(parents=True)
        review = pe_dir / "REVIEW_PE-OPS-GITHUB-SKILLS-01.md"
        review.write_text(
            "# REVIEW\n\n"
            "### Failure classes addressed\n\n"
            "### Evidence\n\n"
            "Evidence block here\n\n"
            "### Verdict\n\n"
            "PASS\n"
        )
        result = MODULE.check_review_schema(base_dir=str(tmp_path))
        assert result["status"] == "PASS"

    def test_fail_missing_headings(self, tmp_path):
        """When REVIEW file is missing required headings, should FAIL."""
        pe_dir = tmp_path / ".elis" / "pe" / "PE-OPS-GITHUB-SKILLS-01"
        pe_dir.mkdir(parents=True)
        review = pe_dir / "REVIEW_PE-OPS-GITHUB-SKILLS-01.md"
        review.write_text("# REVIEW\n\nMissing required sections\n")
        result = MODULE.check_review_schema(base_dir=str(tmp_path))
        assert result["status"] == "FAIL"
        assert result["class"] == MODULE.REVIEW_SCHEMA_NONCOMPLIANT

    def test_pass_no_review_files(self, tmp_path):
        """When no REVIEW files exist, should PASS."""
        result = MODULE.check_review_schema(base_dir=str(tmp_path))
        assert result["status"] == "PASS"


# ── Test 11: Unified runner ────────────────────────────────────────────


class TestRunAllChecks:
    """Integration-level tests for run_all_checks."""

    def test_unknown_check_returns_fail(self):
        """An unknown check name should return FAIL."""
        results = MODULE.run_all_checks(checks_to_run=["nonexistent_check"])
        assert len(results) == 1
        assert results[0]["status"] == "FAIL"
        assert "UNKNOWN_CHECK" in str(results[0]["class"])

    def test_output_contains_check_names(self):
        """All result dicts should have the expected keys."""
        results = MODULE.run_all_checks(checks_to_run=["worktree_binding"])
        assert len(results) == 1
        r = results[0]
        assert "check" in r
        assert "class" in r
        assert "status" in r
        assert "detail" in r

    def test_main_exit_code_pass(self, monkeypatch):
        """When all checks pass, main() should return 0."""
        monkeypatch.setattr("sys.argv", ["prog", "--checks", "worktree_binding"])
        monkeypatch.setattr(
            MODULE,
            "run_all_checks",
            lambda *a, **kw: [
                {
                    "check": "test",
                    "class": "TEST",
                    "status": "PASS",
                    "detail": "OK",
                }
            ],
        )
        ec = MODULE.main()
        assert ec == 0

    def test_main_exit_code_fail(self, monkeypatch):
        """When any check fails, main() should return 1."""
        monkeypatch.setattr("sys.argv", ["prog", "--checks", "worktree_binding"])
        monkeypatch.setattr(
            MODULE,
            "run_all_checks",
            lambda *a, **kw: [
                {
                    "check": "test",
                    "class": "TEST",
                    "status": "FAIL",
                    "detail": "Failed",
                }
            ],
        )
        ec = MODULE.main()
        assert ec == 1


# ── Test: ALL_FAILURE_CLASSES set ──────────────────────────────────────


class TestFailureClassConstants:
    """Verify ALL_FAILURE_CLASSES contains all 11 classes."""

    def test_all_failure_classes_present(self):
        """ALL_FAILURE_CLASSES should contain exactly 11 classes."""
        assert len(MODULE.ALL_FAILURE_CLASSES) == 11
        assert MODULE.WRONG_GITHUB_WORKTREE_OR_CLONE in MODULE.ALL_FAILURE_CLASSES
        assert MODULE.PE_BRANCH_LOCKED_BY_OTHER_WORKTREE in MODULE.ALL_FAILURE_CLASSES
        assert MODULE.STALE_LOCAL_PE_BRANCH_HEAD in MODULE.ALL_FAILURE_CLASSES
        assert MODULE.STALE_LOCAL_WORKSPACE_HEAD in MODULE.ALL_FAILURE_CLASSES
        assert MODULE.LOCAL_UNPUSHED_COMMITS_BLOCK_RESET in MODULE.ALL_FAILURE_CLASSES
        assert MODULE.STALE_CHECK_RUN_NOT_CURRENT_HEAD in MODULE.ALL_FAILURE_CLASSES
        assert MODULE.PM_WRONG_RESPONSIBILITY_BOUNDARY in MODULE.ALL_FAILURE_CLASSES
        assert MODULE.SECRET_OUTPUT_RISK in MODULE.ALL_FAILURE_CLASSES
        assert (
            MODULE.PM_GITHUB_WRITE_CAPABILITY_RESTRICTION_REQUIRED
            in MODULE.ALL_FAILURE_CLASSES
        )
        assert MODULE.REVIEW_ARTEFACT_WRONG_PATH in MODULE.ALL_FAILURE_CLASSES
        assert MODULE.REVIEW_SCHEMA_NONCOMPLIANT in MODULE.ALL_FAILURE_CLASSES


# ── Test: README / function signatures ─────────────────────────────────


class TestSignatures:
    """Verify expected check functions exist and have correct signatures."""

    def test_all_checks_in_registry(self):
        """ALL_CHECKS should map all check names to callables."""
        assert "worktree_binding" in MODULE.ALL_CHECKS
        assert "branch_not_locked" in MODULE.ALL_CHECKS
        assert "branch_not_stale" in MODULE.ALL_CHECKS
        assert "no_unpushed_commits" in MODULE.ALL_CHECKS
        assert "ci_status_current_head" in MODULE.ALL_CHECKS
        assert "protected_files" in MODULE.ALL_CHECKS
        assert "no_secret_output" in MODULE.ALL_CHECKS
        assert "merge_approval" in MODULE.ALL_CHECKS
        assert "review_artefact_path" in MODULE.ALL_CHECKS
        assert "review_schema" in MODULE.ALL_CHECKS

    def test_secret_patterns_are_compiled(self):
        """SECRET_PATTERNS should be a list of compiled regexes."""
        for pat in MODULE.SECRET_PATTERNS:
            assert hasattr(pat, "search")

    def test_REVIEW_PATH_PATTERN_correct_path(self):
        """REVIEW_PATH_PATTERN should match canonical REVIEW paths."""
        assert MODULE.REVIEW_PATH_PATTERN.match(
            ".elis/pe/PE-OPS-GITHUB-SKILLS-01/REVIEW_PE-OPS-GITHUB-SKILLS-01.md"
        )
        assert MODULE.REVIEW_PATH_PATTERN.match(".elis/pe/PE-OPS-A2A-01/REVIEW.md")

    def test_REVIEW_PATH_PATTERN_wrong_path(self):
        """REVIEW_PATH_PATTERN should reject wrong paths."""
        assert not MODULE.REVIEW_PATH_PATTERN.match(
            "docs/ops/REVIEW_PE-OPS-GITHUB-SKILLS-01.md"
        )
        assert not MODULE.REVIEW_PATH_PATTERN.match("some/other/path/REVIEW.md")

    def test_REVIEW_REQUIRED_HEADINGS_defined(self):
        """REVIEW_REQUIRED_HEADINGS should list expected headings."""
        assert "### Evidence" in MODULE.REVIEW_REQUIRED_HEADINGS
        assert "### Verdict" in MODULE.REVIEW_REQUIRED_HEADINGS
        assert "### Failure classes addressed" in MODULE.REVIEW_REQUIRED_HEADINGS
