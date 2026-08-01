"""
ELIS Supervisor — Agent Card definition.

Constructs the official A2A AgentCard protobuf object for the ELIS Supervisor
agent.  Localhost-only: ``url`` is always ``http://127.0.0.1:9501``.
No public bind.  No production service install.
"""

from a2a.types import AgentCard
from a2a.utils.proto_utils import ParseDict

from elis.a2a.supervisor.agent_skill import SUPERVISOR_SKILL_DICT

# Localhost-only base URL — never 0.0.0.0 or a public host.
SUPERVISOR_BASE_URL: str = "http://127.0.0.1:9501"
SUPERVISOR_RPC_PATH: str = "/a2a"
# Full RPC endpoint URL — ClientFactory.create() posts to supported_interfaces[0].url
# verbatim, so this must be the complete endpoint path, not just the base URL.
SUPERVISOR_RPC_URL: str = (
    SUPERVISOR_BASE_URL + SUPERVISOR_RPC_PATH
)  # 'http://127.0.0.1:9501/a2a'

# fmt: off
_SUPERVISOR_CARD_DICT: dict = {
    'name': 'ELIS Supervisor',
    'description': (
        'ELIS Supervisor A2A endpoint.  Provides operational and diagnostic '
        'capability to ELIS PM via the official A2A JSON-RPC protocol.'
    ),
    'version': '0.1.0',
    'capabilities': {
        'streaming': False,
        'push_notifications': False,
    },
    'skills': [SUPERVISOR_SKILL_DICT],
    'supported_interfaces': [
        {
            'url': SUPERVISOR_RPC_URL,
            # Must be 'JSONRPC' — matches TransportProtocol.JSONRPC (StrEnum).
            # ClientFactory.create() compares i.protocol_binding against
            # TransportProtocol values using string equality; 'A2A_JSONRPC_1_0'
            # does not match and causes 'no compatible transports found'.
            'protocol_binding': 'JSONRPC',
            'protocol_version': '1.0',
        }
    ],
    'default_input_modes': ['application/json'],
    'default_output_modes': ['application/json'],
}
# fmt: on


def build_agent_card() -> AgentCard:
    """Return the canonical ELIS Supervisor AgentCard protobuf object."""
    return ParseDict(_SUPERVISOR_CARD_DICT, AgentCard())
