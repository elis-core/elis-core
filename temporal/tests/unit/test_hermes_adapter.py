"""Unit tests for the Hermes Adapter — exercised against a fake `hermes`
binary on PATH so these tests run fast and deterministically without
actually invoking an LLM. A real-invocation smoke test lives in
tests/integration/test_hermes_adapter_live.py instead."""

from __future__ import annotations

import os
import stat
import textwrap

import pytest

from elis_temporal.adapter.hermes.adapter import run_agent


def _install_fake_hermes(tmp_path, script: str):
    fake_bin_dir = tmp_path / "fakebin"
    fake_bin_dir.mkdir()
    fake_hermes = fake_bin_dir / "hermes"
    fake_hermes.write_text(script)
    fake_hermes.chmod(fake_hermes.stat().st_mode | stat.S_IEXEC)
    return fake_bin_dir


def test_run_agent_success(tmp_path, monkeypatch):
    script = textwrap.dedent(
        """\
        #!/usr/bin/env python3
        import os, sys
        assert os.environ.get("HERMES_PROFILE") == "elis-pm"
        print("ok: structured result text")
        sys.exit(0)
        """
    )
    fake_bin_dir = _install_fake_hermes(tmp_path, script)
    monkeypatch.setenv("PATH", f"{fake_bin_dir}:{os.environ['PATH']}")

    result = run_agent(
        profile="elis-pm",
        execution_id="exec-1",
        instructions="do the thing",
    )

    assert result.status == "completed"
    assert result.structured_result == "ok: structured result text"
    assert result.failure_class is None
    assert result.runtime_identity.hermes_profile_env == "elis-pm"
    assert result.correlation_id  # auto-generated when not supplied


def test_run_agent_nonzero_exit_is_failed(tmp_path, monkeypatch):
    script = textwrap.dedent(
        """\
        #!/usr/bin/env python3
        import sys
        print("partial output", file=sys.stdout)
        print("boom", file=sys.stderr)
        sys.exit(2)
        """
    )
    fake_bin_dir = _install_fake_hermes(tmp_path, script)
    monkeypatch.setenv("PATH", f"{fake_bin_dir}:{os.environ['PATH']}")

    result = run_agent(profile="elis-advisor", execution_id="exec-2", instructions="validate")

    assert result.status == "failed"
    assert result.failure_class == "hermes_exit_2"
    assert "boom" in result.usage["stderr_tail"]


def test_run_agent_timeout(tmp_path, monkeypatch):
    script = textwrap.dedent(
        """\
        #!/usr/bin/env python3
        import time
        time.sleep(5)
        """
    )
    fake_bin_dir = _install_fake_hermes(tmp_path, script)
    monkeypatch.setenv("PATH", f"{fake_bin_dir}:{os.environ['PATH']}")

    result = run_agent(
        profile="elis-supervisor",
        execution_id="exec-3",
        instructions="slow thing",
        timeout_seconds=1,
    )

    assert result.status == "timeout"
    assert result.failure_class == "timeout"


def test_run_agent_binary_not_found(monkeypatch):
    monkeypatch.setenv("PATH", "/nonexistent")
    result = run_agent(profile="elis-github", execution_id="exec-4", instructions="push")
    assert result.status == "failed"
    assert result.failure_class == "hermes_binary_not_found"


def test_correlation_id_is_propagated(tmp_path, monkeypatch):
    script = "#!/usr/bin/env python3\nimport sys; sys.exit(0)\n"
    fake_bin_dir = _install_fake_hermes(tmp_path, script)
    monkeypatch.setenv("PATH", f"{fake_bin_dir}:{os.environ['PATH']}")

    result = run_agent(
        profile="elis-pm",
        execution_id="exec-5",
        instructions="x",
        correlation_id="my-fixed-id",
    )
    assert result.correlation_id == "my-fixed-id"
