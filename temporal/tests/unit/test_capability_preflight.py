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

    # CORRECTED: po_approved=True is necessary but not sufficient. The real
    # gh-agentd broker path is not reachable today (Option-A / t_5d9a121f
    # still blocked), so this must still WAIT even with PO approval — the
    # original version of this test asserted ALLOW here, which encoded the
    # false-ALLOW bug as a passing test. availability is checked against the
    # real host state deliberately, not mocked, to prove the fix actually
    # closes the gap rather than just asserting a mock returns what we want.
    po_approved_but_still_unavailable = check_capability_preflight(
        "elis-github",
        required_capabilities=("github_app_credential",),
        proposed_action="pr_merge",
        po_approved=True,
        env={},
    )
    assert po_approved_but_still_unavailable.decision == "WAITING_FOR_CAPABILITY"
    github_cond = po_approved_but_still_unavailable.capability_conditions[0]
    assert github_cond.capability == "github_app_credential"
    assert github_cond.declared is True
    assert github_cond.authorized is True  # po_approved=True satisfies the authorization half
    assert github_cond.available is False  # but the sanctioned path is genuinely unreachable today
    assert github_cond.executable is False


def test_declared_authorized_but_unavailable_waits():
    """(a) declared + authorized + unavailable -> WAITING_FOR_CAPABILITY,
    using an injected probe so this is deterministic regardless of real
    host gh-agentd state."""
    verdict = check_capability_preflight(
        "elis-github",
        required_capabilities=("github_app_credential",),
        proposed_action="pr_merge",
        po_approved=True,
        env={},
        availability_probes={"github_app_credential": lambda: False},
    )
    assert verdict.decision == "WAITING_FOR_CAPABILITY"
    cond = verdict.capability_conditions[0]
    assert (cond.declared, cond.authorized, cond.available) == (True, True, False)


def test_unauthorized_waits_regardless_of_availability():
    """(b) unauthorized (missing PO approval for merge) -> waits, even if
    the underlying path is (hypothetically) available -- authorization and
    availability are independent gates, both required."""
    verdict = check_capability_preflight(
        "elis-github",
        required_capabilities=("github_app_credential",),
        proposed_action="pr_merge",
        po_approved=False,
        env={},
        availability_probes={"github_app_credential": lambda: True},  # hypothetically available
    )
    assert verdict.decision == "WAITING_FOR_CAPABILITY"
    cond = verdict.capability_conditions[0]
    assert cond.available is True  # available...
    assert cond.authorized is False  # ...but not authorized, so still not executable
    assert cond.executable is False


def test_declared_authorized_available_is_eligible():
    """(c) declared + authorized + available -> ALLOW. Only reachable via
    an injected probe override, since the real gh-agentd path is not
    available on this host today -- this proves the ALLOW path genuinely
    works when all three conditions hold, not just that WAITING_FOR_CAPABILITY
    is the only reachable outcome."""
    verdict = check_capability_preflight(
        "elis-github",
        required_capabilities=("github_app_credential",),
        proposed_action="pr_merge",
        po_approved=True,
        env={},
        availability_probes={"github_app_credential": lambda: True},
    )
    assert verdict.decision == "ALLOW"
    cond = verdict.capability_conditions[0]
    assert (cond.declared, cond.authorized, cond.available, cond.executable) == (True, True, True, True)


def test_personal_credential_fallback_never_flips_unavailable_to_available():
    """(d) presence of a personal credential must never change `available`
    to True, and must never allow the request even if authorization/
    availability would otherwise be satisfied."""
    verdict = check_capability_preflight(
        "elis-github",
        required_capabilities=("github_app_credential",),
        proposed_action="pr_merge",
        po_approved=True,
        env={"GH_TOKEN": "ghp_personal_leaked_token"},
        availability_probes={"github_app_credential": lambda: True},  # genuinely available...
    )
    # ...but a personal credential is present, so it must still wait.
    assert verdict.decision == "WAITING_FOR_CAPABILITY"
    cond = verdict.capability_conditions[0]
    assert cond.available is True  # the probe truthfully reports available=True
    assert cond.executable is True  # the capability itself would be executable...
    # ...but the overall verdict is still WAITING_FOR_CAPABILITY because of
    # the separate, always-checked personal-credential rejection reason:
    assert any("personal-credential" in r for r in verdict.reasons)


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
