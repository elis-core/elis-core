"""ELIS semantic Temporal Workflow identity scheme (T2).

Deliberately does NOT invent a competing dedup mechanism. Temporal already
enforces Workflow ID uniqueness per Namespace and offers
``WorkflowIDReusePolicy`` to control what happens when a start is attempted
against an ID with prior history -- the ELIS-specific work here is choosing
a deterministic ID *string* (so equivalent logical work always maps to the
same ID) and the right reuse policy per intent, not building a second
identity system alongside Temporal's own.

Scheme: ``ELIS/<domain>/<process>/<semantic-key>``

  domain        -- e.g. "core", "research", "slr" (matches ELIS board/domain
                    naming already in use elsewhere on this platform)
  process       -- e.g. "gated-pipeline", "profile-lock", "routing"
  semantic-key  -- caller-supplied, must uniquely identify one logical unit
                    of work within (domain, process) -- e.g. a Kanban task
                    id, a PR number, a paper/section identifier. This
                    module does not invent semantic keys; it only shapes,
                    validates and joins them.

Retry vs. correction vs. distinct work, resolved via ID + reuse policy, not
LLM prose or a side table:

  retry of the same logical work (e.g. re-request after transient failure)
      -> SAME semantic key -> SAME Workflow ID -> start with
         ``WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY``: Temporal
         itself refuses to start a new run if the prior run is still
         running or already succeeded, and only allows a new run if the
         prior one is in a *failed/canceled/terminated/timed-out* state.
         This makes "duplicate retry creates duplicate logical execution"
         structurally impossible, not just discouraged.

  correction / revalidation of the same logical work
      -> SAME Workflow ID, and NOT a new Workflow start at all -- it is
         expressed as a Signal/Update against the *existing, still-open*
         run (see workflows/gated_pipeline_workflow.py's
         ``request_correction`` signal). There is deliberately no reuse
         policy that models "correction" as a policy value, because a
         correction is not a new start.

  genuinely distinct work
      -> DIFFERENT semantic key (caller's responsibility to pick one that
         actually differs -- e.g. a different Kanban task id) -> different
         Workflow ID -> no collision possible, concurrent starts are
         independent by construction.

  concurrent equivalent starts (two callers race to start "the same" work)
      -> both attempt the SAME Workflow ID with
         ``WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY`` (or, at the
         client layer, ``WorkflowIDConflictPolicy.USE_EXISTING`` for a
         get-or-create pattern) -- Temporal's server-side ID uniqueness
         guarantee is what reuses/rejects the second start, not a
         client-side race-prone check-then-act.

See docs/ELIS-TEMPORAL-WORKFLOW-IDENTITY-POLICY.md for the full policy
writeup this module implements.
"""

from __future__ import annotations

import dataclasses
import re
from typing import Literal

from temporalio.common import WorkflowIDReusePolicy

_COMPONENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

WorkflowIntent = Literal["initial", "retry", "distinct"]


class InvalidWorkflowIdentityComponent(ValueError):
    pass


def _validate_component(name: str, value: str) -> None:
    if not value or not _COMPONENT_RE.match(value):
        raise InvalidWorkflowIdentityComponent(
            f"{name}={value!r} is not a valid ELIS Workflow identity component "
            f"(must be non-empty, no '/', matches {_COMPONENT_RE.pattern!r})"
        )


@dataclasses.dataclass(frozen=True)
class SemanticWorkflowId:
    domain: str
    process: str
    semantic_key: str

    def __post_init__(self) -> None:
        _validate_component("domain", self.domain)
        _validate_component("process", self.process)
        _validate_component("semantic_key", self.semantic_key)

    @property
    def value(self) -> str:
        return f"ELIS/{self.domain}/{self.process}/{self.semantic_key}"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


def build_semantic_workflow_id(domain: str, process: str, semantic_key: str) -> str:
    """Convenience wrapper: validate + join in one call, returning the
    Workflow ID string directly (the common case for callers that don't
    need the structured ``SemanticWorkflowId`` object)."""
    return SemanticWorkflowId(domain=domain, process=process, semantic_key=semantic_key).value


def id_reuse_policy_for_intent(intent: WorkflowIntent) -> WorkflowIDReusePolicy:
    """Only two real policy values are meaningful here -- see module
    docstring for why "correction" is deliberately not a start-time policy
    at all, and why "distinct" needs no special reuse policy (a distinct
    semantic key already produces a distinct ID, no collision to police)."""
    if intent in ("initial", "retry"):
        return WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY
    if intent == "distinct":
        return WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY
    raise ValueError(f"unknown intent {intent!r}")
