"""
ELIS GitHub — Agent Executor.

Implements the AgentExecutor ABC from the official a2a-sdk.

Official SDK pattern (a2a-sdk 1.1.0):
  - ``execute(self, context, event_queue)`` — second arg is ``EventQueue``,
    NOT a ``TaskUpdater``.  The framework (``LegacyRequestHandler``) passes the
    raw queue; the executor is responsible for constructing a ``TaskUpdater``
    itself if it wants the convenience wrapper.
  - For a new request, ``context.current_task`` is ``None``.
    ``context.task_id`` and ``context.context_id`` are always populated by
    ``RequestContext.__init__`` (generated if absent).
  - The executor must enqueue a ``Task`` proto first (Task-first protocol path),
    then use ``TaskUpdater`` for lifecycle updates.

No external service calls, no governance actions, no production work
executed directly by this executor.  GitHub operations are performed
by the ELIS GitHub agent process; this executor provides the A2A
channel acknowledgement and governance envelope only.
"""

import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks.task_updater import TaskUpdater
from a2a.types import Part, Task, TaskState
from a2a.utils.proto_utils import ParseDict

from elis.a2a.policy import validate_message

logger = logging.getLogger(__name__)


class GitHubExecutor(AgentExecutor):
    """
    ELIS GitHub executor — official SDK pattern.

    On ``execute``:
      1. Retrieve ``context.current_task`` (``None`` for a fresh request).
      2. If no task exists, create one from ``context.task_id`` /
         ``context.context_id`` and enqueue it on ``event_queue``.
      3. Construct ``TaskUpdater(event_queue, task_id, context_id)``.
      4. Use ``TaskUpdater`` for all lifecycle updates.

    On ``cancel``: cancels immediately with no side-effects.
    """

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Handle an incoming A2A task using the official SDK event-queue pattern.
        """
        # Step 1 — retrieve IDs; always populated by RequestContext.__init__
        task_id: str = context.task_id  # type: ignore[assignment]
        context_id: str = context.context_id  # type: ignore[assignment]

        logger.info(
            "GitHubExecutor.execute called — task_id=%s context_id=%s",
            task_id,
            context_id,
        )

        # Step 2 — Task-first: enqueue a Task proto if no existing task
        task = context.current_task
        if task is None:
            task = ParseDict(
                {
                    "id": task_id,
                    "context_id": context_id,
                    "status": {
                        "state": TaskState.Value("TASK_STATE_SUBMITTED"),
                    },
                },
                Task(),
            )
            await event_queue.enqueue_event(task)
            logger.debug("GitHubExecutor: enqueued new Task id=%s", task_id)

        # Step 3 — construct TaskUpdater as a convenience wrapper
        task_updater = TaskUpdater(event_queue, task_id, context_id)

        # ── Gate 2E + Gate 3: policy validation ─────────────────────────
        metadata = context.message.metadata if context.message else None
        sender_role = None
        message_type = None
        elis_sent_at = None
        elis_target_role = None
        sender_token = None
        if metadata is not None:
            if "elis_sender_role" in metadata:
                sender_role = metadata["elis_sender_role"]  # type: ignore[assignment]
            if "elis_message_type" in metadata:
                message_type = metadata["elis_message_type"]  # type: ignore[assignment]
            if "elis_sent_at" in metadata:
                elis_sent_at = metadata["elis_sent_at"]  # type: ignore[assignment]
            if "elis_target_role" in metadata:
                elis_target_role = metadata["elis_target_role"]  # type: ignore[assignment]
            if "elis_sender_token" in metadata:
                sender_token = metadata["elis_sender_token"]  # type: ignore[assignment]

        result = validate_message(
            sender_role=sender_role,  # type: ignore[arg-type]
            message_type=message_type,  # type: ignore[arg-type]
            recipient_role="github",
            declared_target_role=elis_target_role,  # type: ignore[arg-type]
            elis_sent_at=elis_sent_at,  # type: ignore[arg-type]
            sender_token=sender_token,  # type: ignore[arg-type]
        )

        if not result.allowed:
            rejection_part = ParseDict({"text": result.rejection_text}, Part())
            rejection_msg = task_updater.new_agent_message(
                parts=[rejection_part],
                metadata={
                    "elis_rejection_code": result.rejection_code,
                    "elis_policy_version": "1.0.0",
                },
            )
            await task_updater.reject(message=rejection_msg)
            logger.info(
                "GitHubExecutor: rejected — code=%s task_id=%s",
                result.rejection_code,
                task_id,
            )
            return
        # ── End Gate 2E ──────────────────────────────────────────────

        # Step 4 — lifecycle: working → complete with acknowledgement
        await task_updater.start_work()

        ack_text = (
            "ELIS GitHub: acknowledgement received via A2A channel. "
            "This is a diagnostic response confirming the channel is operational. "
            "GitHub operations are dispatched to the ELIS GitHub agent process."
        )
        part: Part = ParseDict({"text": ack_text}, Part())
        from datetime import datetime, timezone as _tz
        response_message = task_updater.new_agent_message(
            parts=[part],
            metadata={
                "elis_sender_role": "github",
                "elis_message_type": "ack",
                "elis_policy_version": "1.0.0",
                "elis_processed_at": datetime.now(_tz.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
            },
        )
        await task_updater.complete(message=response_message)

        logger.info(
            "GitHubExecutor.execute complete — task_id=%s",
            task_id,
        )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Cancel the task immediately."""
        task_id: str = context.task_id  # type: ignore[assignment]
        context_id: str = context.context_id  # type: ignore[assignment]
        logger.info(
            "GitHubExecutor.cancel called — task_id=%s",
            task_id,
        )
        task_updater = TaskUpdater(event_queue, task_id, context_id)
        await task_updater.cancel()
