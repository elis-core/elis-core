"""
elis.a2a.task_store_config — configurable persistence location for an A2A
adapter's ``DatabaseTaskStore``.

Each per-agent server module (``elis.a2a.<role>.server``) previously
hard-coded its own SQLite path under ``/opt/elis/local/`` directly in the
``create_async_engine(...)`` call. This module factors that decision out
into one small, agent-agnostic function: the adapter code does not need to
know which ELIS agent it belongs to, only its own legacy default path (for
transitional compatibility — see ``resolve_task_store_path``'s docstring).

Interface: ``ELIS_A2A_TASK_STORE_PATH`` — an absolute filesystem path to the
SQLite database file (not a directory). Chosen over a full SQLAlchemy URL
(``ELIS_A2A_TASK_STORE_URL``) because every current and near-term-planned
deployment of this adapter is SQLite-backed, and a bare path is simpler to
validate, simpler to reason about for the "parent directory must exist and
be writable" requirement, and matches the target production example
(``ELIS_A2A_TASK_STORE_PATH=/var/lib/elis/hermes/elis-core/<agent>/state/a2a/task_store.db``)
exactly. If a genuinely different backend is ever needed, that is a larger,
separate change — not something this minimal remediation should anticipate.

Fail-closed policy (deliberate choice, see architecture note below):
  - ``ELIS_A2A_TASK_STORE_PATH`` UNSET -> falls back to the caller-supplied
    ``legacy_default_path`` (transitional compatibility only, so the
    CURRENT still-running, unmigrated A2A servers keep working exactly as
    before if this source is ever picked up without every deployment site
    having been updated). This is the one intentionally silent case, and it
    is intentionally narrow: unset means "behave exactly as before,"
    nothing more.
  - ``ELIS_A2A_TASK_STORE_PATH`` SET but invalid (relative, empty, parent
    directory missing, parent directory not writable, or an existing
    filesystem object at the target path that is not a plain regular file —
    see "Existing-path type validation" below) -> raises
    ``TaskStoreConfigError`` immediately. An explicit-but-broken
    configuration must never silently fall back to the legacy default —
    that would silently recreate shared mutable state in what is meant to
    be an isolated, per-agent runtime, which is exactly the failure mode
    this remediation exists to close off.

Deployment responsibility, not this module's: the new, per-agent isolated
systemd unit (a separate, later change — not part of this candidate) MUST
set ``ELIS_A2A_TASK_STORE_PATH`` explicitly to that agent's own dedicated
path under ``/var/lib/elis/hermes/elis-core/<agent>/state/a2a/``. This
module cannot and does not enforce that a deployment did so — it only
guarantees that whatever value IS supplied is either the safe legacy
default or a validated, explicit path; it never fabricates a "looks
isolated but silently isn't" state.

This module does not create, chmod, or chown any directory. The containing
directory is expected to already exist and already be writable by the
service identity the adapter runs as — that is a deployment/systemd
concern, not something A2A source code should be trusted to mutate (OS
permissions remain the actual privilege boundary; see the accepted design
principle this candidate was scoped against).

Safe SQLAlchemy URL construction (v2 fix — HIGH finding from independent
review of v1):
  v1 built the engine URL with a manual f-string,
  ``f"sqlite+aiosqlite:///{path}"``. A filesystem path containing a ``?``
  character is syntactically indistinguishable, in that hand-built string,
  from the start of a URL query component — SQLAlchemy's URL parser split
  a path like ``/state/weird?name=1.db`` into
  ``database="/state/weird"`` + ``query={"name": "1.db"}``, so SQLite
  created (or opened) a file named ``weird``, not the file the caller
  actually configured. This is fixed by never hand-building the URL string
  at all: ``resolve_task_store_url`` now returns a
  ``sqlalchemy.engine.URL`` object built via ``URL.create(..., database=path)``,
  which treats the entire path as an opaque database-identifier field and
  never interprets any character in it as URL syntax. Verified end-to-end
  (not merely by inspecting the URL object) that a path containing
  ``?``/``#``/``%``/space/Unicode characters produces exactly that
  filename on disk — see ``tests/test_a2a_task_store_config.py``.
  ``create_async_engine`` accepts a ``URL`` object directly (this is the
  normal, supported SQLAlchemy usage), so no caller needs to stringify it.

Existing-path type validation (v2 fix — MEDIUM finding from independent
review of v1):
  v1 only validated the PARENT directory of a configured path; it never
  inspected the configured path's own leaf if something was already there.
  A configured path that already existed as a directory, a symlink (to
  anywhere), a FIFO, a socket, or a block/character device would have been
  handed straight to SQLite, with unpredictable (and potentially unsafe —
  e.g. following a symlink to a location the caller did not intend)
  results. v2 uses ``os.lstat`` (never following a symlink) to classify
  whatever already exists at the configured path, BEFORE accepting it:
  a pre-existing plain regular file is accepted (the normal restart case);
  anything else (directory, symlink, FIFO, socket, block device, character
  device, or any other special file type) is refused with
  ``TaskStoreConfigError``.
"""

from __future__ import annotations

import os
import stat

from sqlalchemy.engine import URL

ENV_VAR_TASK_STORE_PATH = "ELIS_A2A_TASK_STORE_PATH"


class TaskStoreConfigError(RuntimeError):
    """Raised when an explicitly supplied task-store configuration is
    invalid. Never raised for an unset configuration — that case uses the
    legacy default instead (see module docstring)."""


_SPECIAL_TYPE_NAMES = (
    (stat.S_ISFIFO, "a FIFO (named pipe)"),
    (stat.S_ISSOCK, "a Unix domain socket"),
    (stat.S_ISBLK, "a block device"),
    (stat.S_ISCHR, "a character device"),
)


def _describe_existing_non_regular(mode: int) -> str:
    """Human-readable description of what's actually at a path, for a
    clear refusal message. Callers only invoke this after already ruling
    out symlink/directory/regular-file, so this only needs to name the
    remaining special-file classes (plus a generic fallback)."""
    for predicate, name in _SPECIAL_TYPE_NAMES:
        if predicate(mode):
            return name
    return f"an unrecognized special filesystem object (mode={oct(mode)})"


def resolve_task_store_path(*, legacy_default_path: str) -> str:
    """Resolve the absolute SQLite file path to use for this adapter's task
    store.

    Args:
        legacy_default_path: the path this specific agent's adapter used
            before this remediation (e.g.
            ``/opt/elis/local/a2a_task_store_advisor.db``). Supplied by the
            caller so this module never needs to know which agent it is
            configuring — it is not a fallback this module invents on its
            own.

    Returns:
        An absolute filesystem path, validated when explicitly configured.

    Raises:
        TaskStoreConfigError: if ``ELIS_A2A_TASK_STORE_PATH`` is set but is
            not usable — not absolute, empty/whitespace, contains a NUL
            byte, its parent directory does not exist or is not writable,
            or a filesystem object already exists at the path and is not a
            plain regular file (see module docstring, "Existing-path type
            validation"). Never falls back to ``legacy_default_path`` in
            any of these cases — an explicit, invalid configuration is
            always a hard failure.
    """
    configured = os.environ.get(ENV_VAR_TASK_STORE_PATH)
    if configured is None:
        return legacy_default_path

    path = configured.strip()
    if not path:
        raise TaskStoreConfigError(
            f"{ENV_VAR_TASK_STORE_PATH} is set but empty/whitespace-only. "
            "Unset it entirely to use the legacy default, or supply a real absolute path."
        )
    if "\x00" in path:
        raise TaskStoreConfigError(f"{ENV_VAR_TASK_STORE_PATH} contains a NUL byte.")
    if not os.path.isabs(path):
        raise TaskStoreConfigError(
            f"{ENV_VAR_TASK_STORE_PATH} must be an absolute path, got {path!r}."
        )

    parent = os.path.dirname(path)
    if not parent:
        raise TaskStoreConfigError(
            f"{ENV_VAR_TASK_STORE_PATH} has no containing directory: {path!r}."
        )
    if not os.path.isdir(parent):
        raise TaskStoreConfigError(
            f"{ENV_VAR_TASK_STORE_PATH} parent directory does not exist or is not a "
            f"directory: {parent!r}. This module does not create it — the deployment "
            "must pre-provision it, writable by the service identity."
        )
    if not os.access(parent, os.W_OK):
        raise TaskStoreConfigError(
            f"{ENV_VAR_TASK_STORE_PATH} parent directory is not writable by this "
            f"process: {parent!r}."
        )

    # Existing-path type validation: classify (without following a
    # symlink) whatever already exists at the leaf itself, if anything.
    if os.path.lexists(path):
        leaf_stat = os.lstat(path)
        mode = leaf_stat.st_mode
        if stat.S_ISLNK(mode):
            raise TaskStoreConfigError(
                f"{ENV_VAR_TASK_STORE_PATH} already exists as a symlink, refusing "
                f"(never followed to its target): {path!r}."
            )
        if stat.S_ISDIR(mode):
            raise TaskStoreConfigError(
                f"{ENV_VAR_TASK_STORE_PATH} already exists as a directory, not a "
                f"database file: {path!r}."
            )
        if not stat.S_ISREG(mode):
            raise TaskStoreConfigError(
                f"{ENV_VAR_TASK_STORE_PATH} already exists as "
                f"{_describe_existing_non_regular(mode)}, not a regular file: {path!r}."
            )
        # else: an existing plain regular file — the normal restart-and-
        # reopen-the-same-database case. Accepted.

    return path


def resolve_task_store_url(*, legacy_default_path: str) -> URL:
    """Resolve the full SQLAlchemy async-engine URL for this adapter's task
    store, using ``resolve_task_store_path`` for the underlying file path.

    Returns a ``sqlalchemy.engine.URL`` object (not a string) built via
    ``URL.create(..., database=path)`` — never a hand-built string. This is
    the safe SQLAlchemy URL construction primitive: it treats the entire
    resolved path as an opaque database identifier, so no character in the
    path (``?``, ``#``, ``%``, spaces, Unicode, etc.) can be misinterpreted
    as URL syntax (query string, fragment, percent-escape, or otherwise).
    ``create_async_engine`` accepts a ``URL`` object directly; callers
    should pass this return value straight through without stringifying it
    themselves.
    """
    path = resolve_task_store_path(legacy_default_path=legacy_default_path)
    return URL.create("sqlite+aiosqlite", database=path)
