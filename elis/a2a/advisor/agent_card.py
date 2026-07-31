"""
ELIS Advisor — Agent Card definition.

Constructs the official A2A AgentCard protobuf object for the ELIS Advisor
agent.  Localhost-only: ``url`` is always ``http://127.0.0.1:9500``.
No public bind.  No production service install.
"""

from a2a.types import AgentCard
from a2a.utils.proto_utils import ParseDict

from elis.a2a.advisor.agent_skill import ADVISOR_SKILL_DICT

# Localhost-only base URL — never 0.0.0.0 or a public host.
ADVISOR_BASE_URL: str = "http://127.0.0.1:9500"
ADVISOR_RPC_PATH: str = "/a2a"
# Full RPC endpoint URL — ClientFactory.create() posts to supported_interfaces[0].url
# verbatim, so this must be the complete endpoint path, not just the base URL.
ADVISOR_RPC_URL: str = (
    ADVISOR_BASE_URL + ADVISOR_RPC_PATH
)  # "http://127.0.0.1:9500/a2a"

# fmt: off
_AGENT_CARD_DICT: dict = {
    "name": "ELIS Advisor",
    "description": (
        "ELIS Advisor A2A endpoint.  Provides advisory and diagnostic "
        "capability to ELIS PM via the official Google A2A JSON-RPC protocol."
    ),
    "version": "0.1.0",
    "capabilities": {
        "streaming": False,
        "push_notifications": False,
    },
    "skills": [ADVISOR_SKILL_DICT],
    "supported_interfaces": [
        {
            "url": ADVISOR_RPC_URL,
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
    """Return the canonical ELIS Advisor AgentCard protobuf object."""
    return ParseDict(_AGENT_CARD_DICT, AgentCard())
