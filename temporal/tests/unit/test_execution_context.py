from __future__ import annotations

import pytest

from elis_temporal.adapter.hermes.adapter import RuntimeIdentity
from elis_temporal.policies.execution_context import (
    UnknownProfileError,
    check_execution_context,
)


def _identity(hermes_profile_env, systemd_unit=None):
    return RuntimeIdentity(
        os_user="samurai",
        uid=1000,
        pid=12345,
        hermes_profile_env=hermes_profile_env,
        cgroup_path="/user.slice/user-1000.slice/user@1000.service/app.slice/hermes-gateway-elis-pm.service/",
        systemd_unit=systemd_unit or "hermes-gateway-elis-pm.service",
    )


def test_matched_principal_allows():
    verdict = check_execution_context("elis-pm", _identity("elis-pm"))
    assert verdict.allowed is True
    assert verdict.observed_hermes_profile_env == "elis-pm"


def test_mismatched_principal_blocks():
    """This is the exact incident-C shape: assigned elis-github, executed
    under elis-pm's HERMES_PROFILE."""
    verdict = check_execution_context("elis-github", _identity("elis-pm"))
    assert verdict.allowed is False
    assert any("expected 'elis-github'" in r for r in verdict.reasons)


def test_unknown_profile_raises():
    with pytest.raises(UnknownProfileError):
        check_execution_context("elis-not-a-real-profile", _identity("elis-pm"))


def test_github_flags_no_persistent_gateway():
    """elis-github has no live gateway today — the check must surface this
    honestly rather than silently pass or silently hard-fail unrelated to
    the actual HERMES_PROFILE match."""
    verdict = check_execution_context("elis-github", _identity("elis-github"))
    # HERMES_PROFILE matches, so allowed=True, but the caveat must still be recorded.
    assert verdict.allowed is True
    assert any("no persistent gateway" in r for r in verdict.reasons)
