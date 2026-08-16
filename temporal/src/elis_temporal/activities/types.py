"""Plain-data types shared between Activity and Workflow code.

Deliberately isolated in its own module with zero side-effecting imports
(no subprocess/socket/os-touching code) so Workflow code can import it
directly without pulling Temporal's workflow sandbox restrictions into the
whole Hermes Adapter import chain. See workflows/routing_workflow.py.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional


@dataclasses.dataclass
class RunAgentActivityInput:
    profile: str
    execution_id: str
    instructions: str
    input_artifacts: Optional[dict[str, Any]] = None
    required_capabilities: Optional[tuple[str, ...]] = None
    execution_context: Optional[dict[str, Any]] = None
    correlation_id: Optional[str] = None
    timeout_seconds: int = 600
