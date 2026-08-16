from __future__ import annotations

import pytest

from elis_temporal.capabilities.preflight import (
    UnknownProfileError,
    check_capability_preflight,
)


def test_allowed_capability_for_profile():
    verdict = check_capability_preflight("elis-pm", required_capabilities=("kanban_write",))
    assert verdict.decision == "ALLOW"


def test_capability_not_granted_to_profile_waits():
    """elis-ideas is not configured for kanban_write — must not crash, must
    return WAITING_FOR_CAPABILITY."""
    verdict = check_capability_preflight("elis-ideas", required_capabilities=("kanban_write",))
    assert verdict.decision == "WAITING_FOR_CAPABILITY"
    assert verdict.reasons


def test_personal_github_token_env_blocks_regardless_of_profile():
    verdict = check_capability_preflight(
        "elis-github",
        required_capabilities=("github_app_credential",),
        env={"GH_TOKEN": "ghp_personal_leaked_token"},
    )
    assert verdict.decision == "WAITING_FOR_CAPABILITY"
    assert any("personal-credential" in r for r in verdict.reasons)


def test_protected_branch_push_never_allowed():
    verdict = check_capability_preflight(
        "elis-github",
        required_capabilities=("github_app_credential",),
        proposed_action="protected_branch_push",
        env={},
    )
    assert verdict.decision == "WAITING_FOR_CAPABILITY"


def test_merge_requires_po_approval():
    denied = check_capability_preflight(
        "elis-github",
        required_capabilities=("github_app_credential",),
        proposed_action="pr_merge",
        po_approved=False,
        env={},
    )
    assert denied.decision == "WAITING_FOR_CAPABILITY"

    allowed = check_capability_preflight(
        "elis-github",
        required_capabilities=("github_app_credential",),
        proposed_action="pr_merge",
        po_approved=True,
        env={},
    )
    assert allowed.decision == "ALLOW"


def test_root_capability_never_allowed_for_ordinary_profile():
    verdict = check_capability_preflight(
        "elis-pm",
        required_capabilities=(),
        proposed_action="host_root_operation_direct_apply",
        env={},
    )
    assert verdict.decision == "WAITING_FOR_CAPABILITY"


def test_unknown_profile_raises():
    with pytest.raises(UnknownProfileError):
        check_capability_preflight("not-a-real-profile", required_capabilities=())
