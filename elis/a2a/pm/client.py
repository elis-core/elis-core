"""
ELIS PM → ELIS Advisor / Supervisor — A2A client scaffold.

Provides the minimal official SDK client path from ELIS PM to ELIS Advisor
and ELIS Supervisor.  Uses:
  - ``A2ACardResolver`` to fetch the agent card from the well-known endpoint
  - ``JsonRpcTransport`` for JSON-RPC message delivery
  - ``Client`` as the top-level send interface
  - ``Struct`` metadata with ``elis_sender_role: "pm"`` for Gate 2E compliance

This is a scaffold: ``send_message`` demonstrates construction of the
client stack with governed PM metadata and verifies the well-known card is
reachable, but does not implement full PM message routing.  That is deferred
to subsequent gates.

Localhost-only: ``base_url`` must be ``http://127.0.0.1:<port>``.
No public URL accepted.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

import httpx
from google.protobuf.struct_pb2 import Struct

from a2a.client.card_resolver import A2ACardResolver
from a2a.client.client import Client
from a2a.client.client_factory import ClientFactory
from a2a.client.transports.jsonrpc import JsonRpcTransport
from a2a.types import AgentCard, Message, Part, SendMessageRequest
from a2a.types import a2a_pb2
from a2a.utils.proto_utils import ParseDict

logger = logging.getLogger(__name__)

_ALLOWED_HOST = "127.0.0.1"
_SENDER_ROLE = "pm"
_POLICY_VERSION = "1.0.0"


def _assert_localhost(url: str) -> None:
    """Raise ValueError if *url* is not a localhost URL."""
    parsed = urlparse(url)
    if parsed.hostname != _ALLOWED_HOST:
        raise ValueError(
            f"Localhost-only policy: host must be '{_ALLOWED_HOST}', "
            f"got {parsed.hostname!r} in {url!r}"
        )


def _build_governed_metadata(
    *,
    message_type: str = "request",
    sender_role: str = _SENDER_ROLE,
    policy_version: str = _POLICY_VERSION,
    task_ref: Optional[str] = None,
) -> Struct:
    """Construct a ``Struct`` with the ELIS governed metadata fields.

    These fields are consumed by ``validate_message()`` in the Gate 2E
    policy module.
    """
    metadata = Struct()
    meta_dict: dict[str, str] = {
        "elis_sender_role": sender_role,
        "elis_message_type": message_type,
        "elis_policy_version": policy_version,
        "elis_sent_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if task_ref:
        meta_dict["elis_task_ref"] = task_ref
    metadata.update(meta_dict)
    return metadata


class AdvisorClient:
    """
    Minimal A2A client scaffold for ELIS PM → ELIS Advisor communication.

    Args:
        base_url: Advisor server base URL.  Must be ``http://127.0.0.1:<port>``.
        rpc_path: JSON-RPC endpoint path (default ``/a2a``).
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:9500",
        rpc_path: str = "/a2a",
    ) -> None:
        _assert_localhost(base_url)
        self.base_url = base_url.rstrip("/")
        self.rpc_url = self.base_url + rpc_path
        self._rpc_path = rpc_path

    async def send_message(
        self,
        client: Client,
        *,
        message_type: str = "request",
        text: str = "ELIS PM diagnostic message.",
        task_ref: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Send a governed PM message via the given ``Client``.

        Constructs ``Struct`` metadata with ``elis_sender_role: "pm"``,
        builds the A2A message, and collects all stream events.

        Args:
            client: A concrete ``Client`` from ``ClientFactory.create(card)``.
            message_type: One of ``"request"``, ``"ack"``, ``"status"``.
            text: The message body text.
            task_ref: Optional task reference for tracing.

        Returns:
            A list of event dicts with keys ``type``, ``state``,
            ``task_id``, ``text``, and ``rejection_code`` (on rejection).
        """
        metadata = _build_governed_metadata(
            message_type=message_type,
            task_ref=task_ref,
        )
        part = ParseDict({"text": text}, Part())
        msg = Message()
        msg.message_id = str(uuid.uuid4())
        msg.context_id = str(uuid.uuid4())
        msg.role = a2a_pb2.Role.Value("ROLE_USER")
        msg.parts.append(part)
        msg.metadata.CopyFrom(metadata)
        req = SendMessageRequest(message=msg)

        events: list[dict[str, Any]] = []
        async for resp in client.send_message(req):
            which = resp.WhichOneof("payload")
            event: dict[str, Any] = {"type": which}
            if which == "task":
                t = resp.task
                state = a2a_pb2.TaskState.Name(t.status.state)
                event["task_id"] = t.id
                event["state"] = state
                if t.status.message:
                    for p in t.status.message.parts:
                        if p.HasField("text"):
                            event["text"] = p.text
                    msg_meta = t.status.message.metadata
                    if msg_meta and "elis_rejection_code" in msg_meta:
                        event["rejection_code"] = msg_meta["elis_rejection_code"]
            elif which == "status_update":
                event["state"] = a2a_pb2.TaskState.Name(resp.status_update.state)
            events.append(event)
        return events

    async def resolve_card(self) -> AgentCard:
        """
        Fetch and return the ELIS Advisor AgentCard from the well-known endpoint.

        Requires a live server at ``self.base_url``.
        """
        async with httpx.AsyncClient(base_url=self.base_url) as http:
            resolver = A2ACardResolver(http, base_url=self.base_url)
            card = await resolver.get_agent_card()
        logger.info(
            "AdvisorClient.resolve_card: resolved card name=%r version=%r",
            card.name,
            card.version,
        )
        return card

    def build_transport(
        self,
        http_client: httpx.AsyncClient,
        card: AgentCard,
    ) -> JsonRpcTransport:
        """
        Construct and return a JsonRpcTransport bound to the given card and HTTP client.

        The caller is responsible for the ``http_client`` lifecycle.
        """
        return JsonRpcTransport(
            httpx_client=http_client,
            agent_card=card,
            url=self.rpc_url,
        )

    def build_client(self, card: AgentCard) -> Client:
        """
        Return a concrete ``Client`` instance via the official SDK factory.

        Uses ``ClientFactory.create(card)`` — the SDK-approved construction
        path.  ``a2a.client.client.Client`` is abstract in a2a-sdk 1.1.0
        and cannot be instantiated directly; ``ClientFactory`` returns a
        ``BaseClient`` (concrete ``Client`` subclass) wired with the
        appropriate transport derived from the card's ``supported_interfaces``.

        Args:
            card: An ``AgentCard`` with at least one compatible interface
                  (protocol_binding='JSONRPC', protocol_version='1.0').

        Returns:
            A concrete ``Client`` instance (``BaseClient``).
        """
        factory = ClientFactory()
        return factory.create(card)

    def __repr__(self) -> str:
        return f"AdvisorClient(base_url={self.base_url!r}, rpc_url={self.rpc_url!r})"


class SupervisorClient:
    """
    Minimal A2A client scaffold for ELIS PM → ELIS Supervisor communication.

    Args:
        base_url: Supervisor server base URL.  Must be ``http://127.0.0.1:<port>``.
        rpc_path: JSON-RPC endpoint path (default ``/a2a``).
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:9501",
        rpc_path: str = "/a2a",
    ) -> None:
        _assert_localhost(base_url)
        self.base_url = base_url.rstrip("/")
        self.rpc_url = self.base_url + rpc_path
        self._rpc_path = rpc_path

    async def send_message(
        self,
        client: Client,
        *,
        message_type: str = "request",
        text: str = "ELIS PM diagnostic message.",
        task_ref: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Send a governed PM message via the given ``Client``.

        Constructs ``Struct`` metadata with ``elis_sender_role: "pm"``,
        builds the A2A message, and collects all stream events.

        Args:
            client: A concrete ``Client`` from ``ClientFactory.create(card)``.
            message_type: One of ``"request"``, ``"ack"``, ``"status"``.
            text: The message body text.
            task_ref: Optional task reference for tracing.

        Returns:
            A list of event dicts with keys ``type``, ``state``,
            ``task_id``, ``text``, and ``rejection_code`` (on rejection).
        """
        metadata = _build_governed_metadata(
            message_type=message_type,
            task_ref=task_ref,
        )
        part = ParseDict({"text": text}, Part())
        msg = Message()
        msg.message_id = str(uuid.uuid4())
        msg.context_id = str(uuid.uuid4())
        msg.role = a2a_pb2.Role.Value("ROLE_USER")
        msg.parts.append(part)
        msg.metadata.CopyFrom(metadata)
        req = SendMessageRequest(message=msg)

        events: list[dict[str, Any]] = []
        async for resp in client.send_message(req):
            which = resp.WhichOneof("payload")
            event: dict[str, Any] = {"type": which}
            if which == "task":
                t = resp.task
                state = a2a_pb2.TaskState.Name(t.status.state)
                event["task_id"] = t.id
                event["state"] = state
                if t.status.message:
                    for p in t.status.message.parts:
                        if p.HasField("text"):
                            event["text"] = p.text
                    msg_meta = t.status.message.metadata
                    if msg_meta and "elis_rejection_code" in msg_meta:
                        event["rejection_code"] = msg_meta["elis_rejection_code"]
            elif which == "status_update":
                event["state"] = a2a_pb2.TaskState.Name(resp.status_update.state)
            events.append(event)
        return events

    async def resolve_card(self) -> AgentCard:
        """
        Fetch and return the ELIS Supervisor AgentCard from the well-known endpoint.

        Requires a live server at ``self.base_url``.
        """
        async with httpx.AsyncClient(base_url=self.base_url) as http:
            resolver = A2ACardResolver(http, base_url=self.base_url)
            card = await resolver.get_agent_card()
        logger.info(
            "SupervisorClient.resolve_card: resolved card name=%r version=%r",
            card.name,
            card.version,
        )
        return card

    def build_transport(
        self,
        http_client: httpx.AsyncClient,
        card: AgentCard,
    ) -> JsonRpcTransport:
        """
        Construct and return a JsonRpcTransport bound to the given card and HTTP client.

        The caller is responsible for the ``http_client`` lifecycle.
        """
        return JsonRpcTransport(
            httpx_client=http_client,
            agent_card=card,
            url=self.rpc_url,
        )

    def build_client(self, card: AgentCard) -> Client:
        """
        Return a concrete ``Client`` instance via the official SDK factory.
        """
        factory = ClientFactory()
        return factory.create(card)

    def __repr__(self) -> str:
        return (
            f"SupervisorClient(base_url={self.base_url!r}, "
            f"rpc_url={self.rpc_url!r})"
        )
