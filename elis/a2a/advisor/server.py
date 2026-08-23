"""
ELIS Advisor — Server wiring.

Assembles the ASGI application for the ELIS Advisor A2A server using the
official SDK components:
  - LegacyRequestHandler (server-side JSON-RPC handler)
  - DatabaseTaskStore (SQLite-backed, survives restart/crash — Tier 2.6)
  - InMemoryQueueManager
  - create_jsonrpc_routes (Starlette routes)

Localhost-only: the ``run()`` helper binds to 127.0.0.1 only.
No 0.0.0.0 bind.  No production service install.

The ASGI ``app`` object is exported so tests can mount it directly via
``httpx.ASGITransport`` without starting a live server.
"""

import logging

from google.protobuf.json_format import MessageToDict
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from sqlalchemy.ext.asyncio import create_async_engine

from a2a.server.events.in_memory_queue_manager import InMemoryQueueManager
from a2a.server.request_handlers.default_request_handler import LegacyRequestHandler
from a2a.server.routes import create_jsonrpc_routes
from a2a.server.tasks.database_task_store import DatabaseTaskStore

from elis.a2a.advisor.agent_card import ADVISOR_RPC_PATH, build_agent_card
from elis.a2a.advisor.executor import AdvisorExecutor
from elis.a2a.task_store_config import resolve_task_store_url

logger = logging.getLogger(__name__)

# ── Build server-side components ──────────────────────────────────────────────

_card = build_agent_card()
_executor = AdvisorExecutor()
# SQLite-backed, survives process restart/crash (Tier 2.6).
#
# The task-store location is configurable via ELIS_A2A_TASK_STORE_PATH (see
# elis.a2a.task_store_config) so a dedicated, isolated per-agent systemd
# unit can point this at its own state directory (e.g.
# /var/lib/elis/hermes/elis-core/elis-advisor/state/a2a/task_store.db)
# instead of the legacy shared /opt/elis/local/ location. When the
# environment variable is unset, this falls back to the historical
# per-role path below for transitional compatibility with the current,
# not-yet-migrated deployment — an explicitly-set-but-invalid value fails
# closed rather than silently falling back.
_LEGACY_TASK_STORE_PATH = "/opt/elis/local/a2a_task_store_advisor.db"
_task_store_url = resolve_task_store_url(legacy_default_path=_LEGACY_TASK_STORE_PATH)
_engine = create_async_engine(_task_store_url)
_task_store = DatabaseTaskStore(engine=_engine)
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
    rpc_url=ADVISOR_RPC_PATH,
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


def run(host: str = "127.0.0.1", port: int = 9500) -> None:
    """
    Start the ELIS Advisor A2A server on localhost.

    This is a development/smoke-test helper only.  Never bind to 0.0.0.0.
    Never install as a production service via this function.

    Args:
        host: Must be '127.0.0.1'.  Any other value raises ValueError.
        port: TCP port number (default 9500).
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

    logger.info("Starting ELIS Advisor A2A server on %s:%d", host, port)
    uvicorn.run(app, host=host, port=port, log_level="info")
