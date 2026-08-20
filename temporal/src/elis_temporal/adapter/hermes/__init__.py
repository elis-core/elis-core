"""Hermes Adapter v1 — the narrow, stable boundary between Temporal and the
Hermes agent runtime.

Temporal Workflow code must never import Hermes internals directly. Everything
Temporal knows about Hermes flows through :func:`run_agent` and the
:class:`AgentResult` it returns. This keeps a future Hermes upgrade a matter of
re-testing this one module against the real CLI, not reconciling an embedded
orchestration patch stack (see HERMES-ADAPTER-CONTRACT.md).
"""

from .adapter import AgentResult, CapabilityResult, RuntimeIdentity, run_agent

__all__ = ["run_agent", "AgentResult", "CapabilityResult", "RuntimeIdentity"]
