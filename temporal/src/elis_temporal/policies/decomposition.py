"""Structured LLM-proposed decomposition -> deterministic Workflow-policy
authorization (T2, plan v2.1 governing rule: "LLM proposes. Temporal
authorizes execution.").

This module is pure/deterministic (no IO, no subprocess, no clock/random
reads) by construction -- it is safe to call directly from Workflow code,
unlike the Hermes Adapter or the capability preflight's socket probe. Its
job is exactly the boundary in workflows/gated_pipeline_workflow.py's
architecture note: an LLM Activity may PROPOSE a decomposition (as a
structured, schema-validated result -- never as raw prose that mutates
topology directly); this function is what actually AUTHORIZES it, and it
does so with the same conservatism as capabilities/preflight.py -- default
deny, explicit reasons, no partial-authorize-then-hope.

Deliberately all-or-nothing per proposal (reject the whole proposal, not a
silently-filtered subset) -- a partial-authorization mode would let an LLM
"fish" for which children pass by resubmitting variations, which is exactly
the kind of ambient trust this boundary exists to prevent. Rationale
recorded, not just asserted: see failing test
test_decomposition_partial_invalidity_rejects_whole_proposal.
"""

from __future__ import annotations

import dataclasses
from typing import Optional

from elis_temporal.profiles.routing import PROFILE_ROUTES

# Bounded topology limit -- an arbitrary but explicit, documented ceiling.
# Plan v2.1 requires *a* bound to exist, not a specific number; 8 was chosen
# as generous headroom over every decomposition actually observed on the
# live elis-core/elis-slr boards (see kanban board surveys in this
# conversation's memory -- typical fan-out is 2-4 children) while still
# being a real, enforced ceiling rather than an unbounded one.
MAX_CHILDREN_PER_PROPOSAL = 8

# Coarse authority ranking used to enforce "child authority_class must not
# exceed parent's" (no privilege escalation via decomposition). Derived
# from the activity-class severity already implicit in
# profiles/routing.py's allowed/prohibited lists -- purely local
# reasoning/notification work ranks lowest, orchestration/validation
# ranks mid, anything mutating/credentialed/host-touching ranks highest.
# Deliberately conservative: unranked/unknown authority_class values sort
# to the top rank (least trusted), never the bottom, so an unrecognized
# authority_class can never slip past the boundary by omission.
_AUTHORITY_RANK: dict[str, int] = {
    "cognitive_reasoning": 0,
    "notification": 0,
    "orchestration_decision": 1,
    "independent_validation": 1,
    "research_domain_work": 1,
    "runtime_platform_change": 2,
    "host_root_operation_packet_only": 2,
    "credential_access": 2,
    "github_mutation": 2,
    "host_root_operation": 2,
}
_UNKNOWN_AUTHORITY_RANK = 3  # highest / least-trusted -- see docstring above


def _authority_rank(authority_class: str) -> int:
    return _AUTHORITY_RANK.get(authority_class, _UNKNOWN_AUTHORITY_RANK)


@dataclasses.dataclass(frozen=True)
class ChildProposal:
    semantic_key: str
    role: str  # ELIS profile name
    purpose: str
    required_capabilities: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()  # semantic_keys of sibling children this depends on
    decomposable: bool = True
    authority_class: str = "cognitive_reasoning"

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class DecompositionProposal:
    decision_id: str
    parent_execution_id: str
    parent_profile: str
    parent_authority_class: str
    proposed_children: tuple[ChildProposal, ...]
    rationale: str

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        return d


@dataclasses.dataclass(frozen=True)
class DecompositionValidationVerdict:
    decision: str  # "AUTHORIZE" | "REJECT"
    decision_id: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def _known_capability_classes() -> frozenset[str]:
    classes: set[str] = set()
    for route in PROFILE_ROUTES.values():
        classes.update(route.capability_classes)
    return frozenset(classes)


def validate_decomposition_proposal(
    proposal: DecompositionProposal,
    *,
    existing_semantic_keys: frozenset[str] = frozenset(),
) -> DecompositionValidationVerdict:
    """Pure, deterministic. Safe to call directly from Workflow code.

    ``existing_semantic_keys`` lets a caller pass in semantic keys already
    materialized for this parent (e.g. from a prior partially-processed
    decomposition) so a resubmitted proposal that tries to recreate an
    already-existing child is caught as a duplicate, not silently
    re-authorized -- this is the "semantic duplicate policy" requirement.
    """
    reasons: list[str] = []
    known_caps = _known_capability_classes()

    if len(proposal.proposed_children) == 0:
        reasons.append("empty decomposition (zero proposed children) is not a decomposition")

    if len(proposal.proposed_children) > MAX_CHILDREN_PER_PROPOSAL:
        reasons.append(
            f"{len(proposal.proposed_children)} proposed children exceeds bounded topology "
            f"limit of {MAX_CHILDREN_PER_PROPOSAL}"
        )

    seen_keys: set[str] = set()
    for child in proposal.proposed_children:
        # -- semantic duplicate policy (within-proposal + against existing) --
        if child.semantic_key in seen_keys:
            reasons.append(f"duplicate semantic_key {child.semantic_key!r} within one proposal")
        seen_keys.add(child.semantic_key)
        if child.semantic_key in existing_semantic_keys:
            reasons.append(
                f"semantic_key {child.semantic_key!r} already exists for this parent "
                f"(duplicate child rejection)"
            )

        # -- recognized ELIS profile / permitted role --
        if child.role not in PROFILE_ROUTES:
            reasons.append(f"child {child.semantic_key!r}: role {child.role!r} is not a recognized ELIS profile")

        # -- no self-validation via decomposition --
        if child.authority_class == "independent_validation" and child.role == proposal.parent_profile:
            reasons.append(
                f"child {child.semantic_key!r}: an independent_validation child cannot share "
                f"its parent's profile ({proposal.parent_profile!r}) -- self-validation"
            )

        # -- capability class exists --
        for cap in child.required_capabilities:
            if cap not in known_caps:
                reasons.append(
                    f"child {child.semantic_key!r}: required_capability {cap!r} is not a known "
                    f"capability class {sorted(known_caps)!r}"
                )

        # -- authority boundary: no privilege escalation via decomposition --
        if _authority_rank(child.authority_class) > _authority_rank(proposal.parent_authority_class):
            reasons.append(
                f"child {child.semantic_key!r}: authority_class {child.authority_class!r} "
                f"(rank {_authority_rank(child.authority_class)}) exceeds parent "
                f"{proposal.parent_authority_class!r} (rank {_authority_rank(proposal.parent_authority_class)}) "
                f"-- privilege escalation via decomposition is never authorized"
            )

    # -- dependency legality: every dependency must reference a sibling in
    # THIS proposal (no forward reference to a nonexistent target, no
    # inventing an external dependency out of thin air) and no self-dependency --
    for child in proposal.proposed_children:
        for dep in child.dependencies:
            if dep == child.semantic_key:
                reasons.append(f"child {child.semantic_key!r}: cannot depend on itself")
            elif dep not in seen_keys:
                reasons.append(
                    f"child {child.semantic_key!r}: dependency {dep!r} does not reference any "
                    f"sibling in this proposal -- illegal dependency"
                )

    decision = "REJECT" if reasons else "AUTHORIZE"
    return DecompositionValidationVerdict(decision=decision, decision_id=proposal.decision_id, reasons=tuple(reasons))
