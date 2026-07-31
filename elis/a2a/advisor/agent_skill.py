"""
ELIS Advisor — Agent Skill definition.

Defines the single diagnostic/acknowledgement skill exposed by the
ELIS Advisor A2A server.  Uses the official SDK protobuf construction
pattern (ParseDict) — never Pydantic kwargs.
"""

from a2a.types import AgentSkill
from a2a.utils.proto_utils import ParseDict

# fmt: off
ADVISOR_SKILL_DICT: dict = {
    "id": "elis-advisor-acknowledge",
    "name": "Acknowledge",
    "description": (
        "Safe diagnostic and acknowledgement skill for ELIS Advisor.  "
        "Accepts a plain-text message from ELIS PM and returns a structured "
        "acknowledgement confirming the A2A channel is operational.  "
        "No governance-sensitive action is taken by this skill."
    ),
    "tags": ["elis", "advisory", "diagnostic"],
    "examples": ["ping", "hello advisor", "ack"],
    "input_modes": ["application/json"],
    "output_modes": ["application/json"],
}
# fmt: on


def build_advisor_skill() -> AgentSkill:
    """Return the canonical ELIS Advisor AgentSkill protobuf object."""
    return ParseDict(ADVISOR_SKILL_DICT, AgentSkill())
