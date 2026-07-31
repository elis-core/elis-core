"""
ELIS GitHub — Server wiring.

Assembles the ASGI application for the ELIS GitHub A2A server using the
official SDK components:
  - LegacyRequestHandler (server-side JSON-RPC handler)
  - InMemoryTaskStore
  - InMemoryQueueManager
  - create_jsonrpc_routes (Starlette routes)

Localhost-only: the ``run()`` helper binds to 127.0.0.1 only.
No 0.0.0.0 bind.

The ASGI ``app`` object is exported so tests can mount it directly via
``httpx.ASGITransport`` without starting a live server.
"""

import logging

from google.protobuf.json_format import MessageToDict
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from a2a.server.events.in_memory_queue_manager import InMemoryQueueManager
from a2a.server.request_handlers.default_request_handler import LegacyRequestHandler
from a2a.server.routes import create_jsonrpc_routes
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore

from elis.a2a.github.agent_card import GITHUB_RPC_PATH, build_agent_card
from elis.a2a.github.executor import GitHubExecutor

logger = logging.getLogger(__name__)

# ── Build server-side components ──────────────────────────────────────────────

_card = build_agent_card()
_executor = GitHubExecutor()
_task_store = InMemoryTaskStore()
_queue_manager = InMemoryQueueManager()

_handler = LegacyRequestHandler(
    agent_executor=_executor,
    task_store=_task_store,
    agent_card=_card,
    queue_manager=_queue_manager,
)

# ── Well-known agent card endpoint ────────────────────────────────────────────


async def _agent_card_endpoint(request: Request) -> JSONResponse:
    """Serve the agent card at /.well-known/agent-card.json."""
    card_dict = MessageToDict(
        _card,
        preserving_proto_field_name=True,
        always_print_fields_with_no_presence=False,
    )
    return JSONResponse(card_dict)


# ── Assemble ASGI app ─────────────────────────────────────────────────────────

_rpc_routes = create_jsonrpc_routes(
    request_handler=_handler,
    rpc_url=GITHUB_RPC_PATH,
    context_builder=None,
    enable_v0_3_compat=False,
)

_well_known_route = Route(
    "/.well-known/agent-card.json",
    endpoint=_agent_card_endpoint,
    methods=["GET"],
)

app = Starlette(
    routes=[_well_known_route, *_rpc_routes],
)


def run(host: str = "127.0.0.1", port: int = 9503) -> None:
    """
    Start the ELIS GitHub A2A server on localhost.

    Never bind to 0.0.0.0.

    Args:
        host: Must be '127.0.0.1'.  Any other value raises ValueError.
        port: TCP port number (default 9503).
    """
    if host != "127.0.0.1":
        raise ValueError(
            f"Localhost-only policy: host must be '127.0.0.1', got {host!r}"
        )
    try:
        import uvicorn  # type: ignore[import]
    except ImportError as exc:
        raise RuntimeError(
            "uvicorn is required to run the server.  "
            "Install it in the runtime venv: uv pip install uvicorn"
        ) from exc

    logger.info("Starting ELIS GitHub A2A server on %s:%d", host, port)
    uvicorn.run(app, host=host, port=port, log_level="info")