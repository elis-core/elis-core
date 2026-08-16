"""Hermes Adapter v1 implementation.

Design choice, deliberate: this Adapter shells out to the real ``hermes -z``
CLI as a subprocess rather than importing ``hermes_cli`` internals into this
process. Two reasons:

1. The CLI surface is Hermes's own stable public contract; internal modules
   (``kanban_db.py``, ``gateway.py``, ...) are not, and change under active
   development (see the Hermes P2 remediation branch this same day, five
   internal-only commits). Coupling to the CLI boundary is what makes a future
   Hermes upgrade an Adapter-compatibility-test problem instead of a
   source-reconciliation problem.
2. It naturally captures real runtime identity (uid, cgroup, systemd unit) of
   the *actual* process that executed the agent, which is exactly what
   execution-context-fidelity checking needs to observe honestly rather than
   assume.

This adapter does not know how to route a task to a specific systemd
unit/cgroup/uid (that is Option-A's — currently blocked, see t_5d9a121f — and
Temporal Task-Queue-to-worker-pool routing's job). It only executes wherever
it is invoked and *reports* what it observes, honestly, so a policy layer can
compare that to what was expected.
"""

from __future__ import annotations

import dataclasses
import getpass
import json
import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Optional

HERMES_BIN = "hermes"
DEFAULT_TIMEOUT_SECONDS = 600


@dataclasses.dataclass(frozen=True)
class RuntimeIdentity:
    """What actually executed this call, observed, not assumed."""

    os_user: str
    uid: int
    pid: int
    hermes_profile_env: Optional[str]
    cgroup_path: Optional[str]
    systemd_unit: Optional[str]

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class CapabilityResult:
    """Result of a pre-execution capability check. Populated by the caller
    (the Temporal Activity wrapper / capability-preflight policy), not by
    this adapter itself — the adapter reports identity, it does not decide
    policy. Included in AgentResult for provenance only."""

    checked: bool
    allowed: bool
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {"checked": self.checked, "allowed": self.allowed, "reasons": list(self.reasons)}


@dataclasses.dataclass(frozen=True)
class AgentResult:
    status: str  # "completed" | "failed" | "timeout" | "blocked"
    structured_result: Optional[str]
    evidence_refs: tuple[str, ...]
    checkpoint: Optional[str]
    usage: dict
    failure_class: Optional[str]
    runtime_identity: RuntimeIdentity
    capability_result: Optional[CapabilityResult]
    correlation_id: str

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["runtime_identity"] = self.runtime_identity.to_dict()
        d["capability_result"] = self.capability_result.to_dict() if self.capability_result else None
        return d


def _observe_runtime_identity(hermes_profile_env: Optional[str]) -> RuntimeIdentity:
    """Observe THIS process's real identity, not a claimed/expected one."""
    cgroup_path = None
    systemd_unit = None
    try:
        raw = Path("/proc/self/cgroup").read_text()
        lines = [ln for ln in raw.splitlines() if ln.strip()]
        if lines:
            cgroup_path = lines[0].split(":", 2)[-1]
            # cgroup v2 paths for a systemd user unit look like:
            # /user.slice/user-1000.slice/user@1000.service/app.slice/<unit>.service/...
            for part in cgroup_path.split("/"):
                if part.endswith(".service"):
                    systemd_unit = part
    except OSError:
        pass

    return RuntimeIdentity(
        os_user=getpass.getuser(),
        uid=os.getuid(),
        pid=os.getpid(),
        hermes_profile_env=hermes_profile_env,
        cgroup_path=cgroup_path,
        systemd_unit=systemd_unit,
    )


def run_agent(
    profile: str,
    execution_id: str,
    instructions: str,
    input_artifacts: Optional[dict[str, Any]] = None,
    required_capabilities: Optional[tuple[str, ...]] = None,
    execution_context: Optional[dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    capability_result: Optional[CapabilityResult] = None,
) -> AgentResult:
    """Invoke Hermes as a real subprocess (``hermes -z``) under the given
    profile and return a structured, Temporal-Activity-friendly result.

    This function is deliberately synchronous and blocking — it is meant to
    be called from inside a Temporal Activity (never Workflow code), where
    the Temporal SDK already runs Activities in a worker thread/process and
    handles the async boundary. Non-determinism (this whole function) must
    never appear inside Workflow code; that boundary is enforced by
    convention here and structurally by where Activities are registered in
    ``activities/``.

    Parameters mirror the plan's Adapter contract exactly:
    profile, execution_id, instructions, input_artifacts,
    required_capabilities, execution_context, correlation_id.
    """
    correlation_id = correlation_id or str(uuid.uuid4())
    input_artifacts = input_artifacts or {}
    required_capabilities = required_capabilities or ()
    execution_context = execution_context or {}

    env = dict(os.environ)
    env["HERMES_PROFILE"] = profile

    started = time.monotonic()
    try:
        proc = subprocess.run(
            [HERMES_BIN, "-z", instructions],
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        runtime_identity = _observe_runtime_identity(env.get("HERMES_PROFILE"))
        return AgentResult(
            status="timeout",
            structured_result=None,
            evidence_refs=(),
            checkpoint=None,
            usage={"elapsed_seconds": time.monotonic() - started},
            failure_class="timeout",
            runtime_identity=runtime_identity,
            capability_result=capability_result,
            correlation_id=correlation_id,
        )
    except FileNotFoundError as exc:
        runtime_identity = _observe_runtime_identity(env.get("HERMES_PROFILE"))
        return AgentResult(
            status="failed",
            structured_result=None,
            evidence_refs=(),
            checkpoint=None,
            usage={"elapsed_seconds": time.monotonic() - started},
            failure_class="hermes_binary_not_found",
            runtime_identity=runtime_identity,
            capability_result=capability_result,
            correlation_id=correlation_id,
        )

    elapsed = time.monotonic() - started
    runtime_identity = _observe_runtime_identity(env.get("HERMES_PROFILE"))

    status = "completed" if proc.returncode == 0 else "failed"
    failure_class = None if proc.returncode == 0 else f"hermes_exit_{proc.returncode}"

    return AgentResult(
        status=status,
        structured_result=proc.stdout.strip() if proc.stdout else None,
        evidence_refs=(),  # populated by the caller from known artifact paths, adapter has no opinion
        checkpoint=None,  # wiring to check_before_claim()-style discovery is a T2 concern, not T1
        usage={
            "elapsed_seconds": elapsed,
            "returncode": proc.returncode,
            "stderr_tail": proc.stderr[-2000:] if proc.stderr else "",
        },
        failure_class=failure_class,
        runtime_identity=runtime_identity,
        capability_result=capability_result,
        correlation_id=correlation_id,
    )
