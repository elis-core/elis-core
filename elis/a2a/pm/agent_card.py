"""
ELIS PM — Agent Card definition.

Constructs the official A2A AgentCard protobuf object for the ELIS PM
agent.  Localhost-only: ``url`` is always ``http://127.0.0.1:9502``.
No public bind.  No production service install.
"""

from a2a.types import AgentCard
from a2a.utils.proto_utils import ParseDict

# ── PM Skill (defined inline — no separate agent_skill.py) ────────────
# fmt: off
PM_SKILL_DICT: dict = {
    "id": "elis-pm-acknowledge",
    "name": "Acknowledge",
    "description": (
        "Safe diagnostic and acknowledgement skill for ELIS PM.  "
        "Accepts a plain-text message and returns a structured "
        "acknowledgement confirming the A2A channel is operational.  "
        "No governance-sensitive action is taken by this skill."
    ),
    "tags": ["elis", "pm", "diagnostic"],
    "examples": ["ping", "hello pm", "ack"],
    "input_modes": ["application/json"],
    "output_modes": ["application/json"],
}
# fmt: on

# ── Agent Card ─────────────────────────────────────────────────────────
# Localhost-only base URL — never 0.0.0.0 or a public host.
PM_BASE_URL: str = "http://127.0.0.1:9502"
PM_RPC_PATH: str = "/a2a"
# Full RPC endpoint URL — ClientFactory.create() posts to supported_interfaces[0].url
# verbatim, so this must be the complete endpoint path, not just the base URL.
PM_RPC_URL: str = PM_BASE_URL + PM_RPC_PATH  # "http://127.0.0.1:9502/a2a"

# fmt: off
_PM_CARD_DICT: dict = {
    "name": "ELIS PM",
    "description": (
        "ELIS PM A2A endpoint.  Provides project management and "
        "orchestration capability to ELIS agents via the official A2A "
        "JSON-RPC protocol."
    ),
    "version": "0.1.0",
    "capabilities": {
        "streaming": False,
        "push_notifications": False,
    },
    "skills": [PM_SKILL_DICT],
    "supported_interfaces": [
        {
            "url": PM_RPC_URL,
            # Must be 'JSONRPC' — matches TransportProtocol.JSONRPC (StrEnum).
            # ClientFactory.create() compares i.protocol_binding against
            # TransportProtocol values using string equality; 'A2A_JSONRPC_1_0'
            # does not match and causes "no compatible transports found".
            "protocol_binding": "JSONRPC",
            "protocol_version": "1.0",
        }
    ],
    "default_input_modes": ["application/json"],
    "default_output_modes": ["application/json"],
}
# fmt: on


def build_agent_card() -> AgentCard:
    """Return the canonical ELIS PM AgentCard protobuf object."""
    return ParseDict(_PM_CARD_DICT, AgentCard())
