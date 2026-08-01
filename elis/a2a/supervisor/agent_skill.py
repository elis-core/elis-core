"""
ELIS Supervisor — Agent Skill definition.

Defines the single diagnostic/acknowledgement skill exposed by the
ELIS Supervisor A2A server.  Uses the official SDK protobuf construction
pattern (ParseDict) — never Pydantic kwargs.
"""

from a2a.types import AgentSkill
from a2a.utils.proto_utils import ParseDict

# fmt: off
SUPERVISOR_SKILL_DICT: dict = {
    'id': 'elis-supervisor-acknowledge',
    'name': 'Acknowledge',
    'description': (
        'Safe diagnostic and acknowledgement skill for ELIS Supervisor.  '
        'Accepts a plain-text message and returns a structured '
        'acknowledgement confirming the A2A channel is operational.  '
        'No governance-sensitive action is taken by this skill.'
    ),
    'tags': ['elis', 'supervisory', 'diagnostic'],
    'examples': ['ping', 'hello supervisor', 'ack'],
    'input_modes': ['application/json'],
    'output_modes': ['application/json'],
}
# fmt: on


def build_supervisor_skill() -> AgentSkill:
    """Return the canonical ELIS Supervisor AgentSkill protobuf object."""
    return ParseDict(SUPERVISOR_SKILL_DICT, AgentSkill())
