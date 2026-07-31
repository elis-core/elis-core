"""
ELIS GitHub — Agent Skill definition.
"""

from a2a.types import AgentSkill
from a2a.utils.proto_utils import ParseDict

# fmt: off
GITHUB_SKILL_DICT: dict = {
    "id": "elis-github-acknowledge",
    "name": "Acknowledge",
    "description": (
        "Safe diagnostic and acknowledgement skill for ELIS GitHub.  "
        "Accepts a plain-text message and returns a structured "
        "acknowledgement confirming the A2A channel is operational.  "
        "No governance-sensitive action is taken by this skill."
    ),
    "tags": ["elis", "github", "diagnostic"],
    "examples": ["ping", "hello github", "ack"],
    "input_modes": ["application/json"],
    "output_modes": ["application/json"],
}
# fmt: on


def build_github_skill() -> AgentSkill:
    """Return the canonical ELIS GitHub AgentSkill protobuf object."""
    return ParseDict(GITHUB_SKILL_DICT, AgentSkill())