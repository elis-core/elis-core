"""
ELIS GitHub — Agent Card definition.

Localhost-only: ``url`` is always ``http://127.0.0.1:9503``.
No public bind.
"""

from a2a.types import AgentCard
from a2a.utils.proto_utils import ParseDict

from elis.a2a.github.agent_skill import GITHUB_SKILL_DICT

GITHUB_BASE_URL: str = "http://127.0.0.1:9503"
GITHUB_RPC_PATH: str = "/a2a"
GITHUB_RPC_URL: str = GITHUB_BASE_URL + GITHUB_RPC_PATH

# fmt: off
_AGENT_CARD_DICT: dict = {
    "name": "ELIS GitHub",
    "description": (
        "ELIS GitHub A2A endpoint.  Diagnostic and acknowledgement channel only.  "
        "No GitHub operations, mutations, or governance actions are performed "
        "through this A2A service."
    ),
    "version": "0.1.0",
    "capabilities": {
        "streaming": False,
        "push_notifications": False,
    },
    "skills": [GITHUB_SKILL_DICT],
    "supported_interfaces": [
        {
            "url": GITHUB_RPC_URL,
            "protocol_binding": "JSONRPC",
            "protocol_version": "1.0",
        }
    ],
    "default_input_modes": ["application/json"],
    "default_output_modes": ["application/json"],
}
# fmt: on


def build_agent_card() -> AgentCard:
    """Return the canonical ELIS GitHub AgentCard protobuf object."""
    return ParseDict(_AGENT_CARD_DICT, AgentCard())