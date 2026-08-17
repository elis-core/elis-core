from __future__ import annotations

from elis_temporal.policies.decomposition import (
    ChildProposal,
    DecompositionProposal,
    MAX_CHILDREN_PER_PROPOSAL,
    validate_decomposition_proposal,
)


def _proposal(children, **overrides):
    defaults = dict(
        decision_id="dec-1",
        parent_execution_id="exec-1",
        parent_profile="elis-pm",
        parent_authority_class="orchestration_decision",
        proposed_children=tuple(children),
        rationale="test",
    )
    defaults.update(overrides)
    return DecompositionProposal(**defaults)


def test_valid_decomposition_authorized():
    """(test ledger item 5) A well-formed proposal against real ELIS
    profiles is authorized."""
    proposal = _proposal(
        [
            ChildProposal(
                semantic_key="child-1",
                role="elis-ideas",
                purpose="draft",
                required_capabilities=(),
                authority_class="cognitive_reasoning",
            ),
        ]
    )
    verdict = validate_decomposition_proposal(proposal)
    assert verdict.decision == "AUTHORIZE"
    assert verdict.reasons == ()


def test_duplicate_child_within_proposal_rejected():
    """(test ledger item 6, part A) two children with the same semantic_key
    in one proposal must reject the whole proposal."""
    proposal = _proposal(
        [
            ChildProposal(semantic_key="dup", role="elis-ideas", purpose="a"),
            ChildProposal(semantic_key="dup", role="elis-ideas", purpose="b"),
        ]
    )
    verdict = validate_decomposition_proposal(proposal)
    assert verdict.decision == "REJECT"
    assert any("duplicate semantic_key" in r for r in verdict.reasons)


def test_duplicate_against_existing_semantic_keys_rejected():
    """(test ledger item 6, part B) resubmitting a proposal that recreates
    an already-materialized child is caught, not silently re-authorized."""
    proposal = _proposal([ChildProposal(semantic_key="already-there", role="elis-ideas", purpose="a")])
    verdict = validate_decomposition_proposal(proposal, existing_semantic_keys=frozenset({"already-there"}))
    assert verdict.decision == "REJECT"
    assert any("already exists" in r for r in verdict.reasons)


def test_invalid_profile_rejected():
    """(test ledger item 7) an unrecognized ELIS profile as a child role
    must reject."""
    proposal = _proposal([ChildProposal(semantic_key="c1", role="not-a-real-elis-profile", purpose="a")])
    verdict = validate_decomposition_proposal(proposal)
    assert verdict.decision == "REJECT"
    assert any("not a recognized ELIS profile" in r for r in verdict.reasons)


def test_self_validation_via_decomposition_rejected():
    """(test ledger item 8) a parent cannot decompose into a child that
    independently-validates the parent's own profile."""
    proposal = _proposal(
        [
            ChildProposal(
                semantic_key="c1",
                role="elis-pm",  # same as parent_profile="elis-pm"
                purpose="validate my own parent",
                authority_class="independent_validation",
            ),
        ],
        parent_profile="elis-pm",
    )
    verdict = validate_decomposition_proposal(proposal)
    assert verdict.decision == "REJECT"
    assert any("self-validation" in r for r in verdict.reasons)


def test_unknown_capability_class_rejected():
    proposal = _proposal(
        [ChildProposal(semantic_key="c1", role="elis-pm", purpose="a", required_capabilities=("made_up_capability",))]
    )
    verdict = validate_decomposition_proposal(proposal)
    assert verdict.decision == "REJECT"
    assert any("not a known capability class" in r for r in verdict.reasons)


def test_authority_escalation_rejected():
    """Child cannot claim a higher authority_class than its parent -- no
    privilege escalation via decomposition."""
    proposal = _proposal(
        [ChildProposal(semantic_key="c1", role="elis-supervisor", purpose="a", authority_class="host_root_operation_packet_only")],
        parent_authority_class="cognitive_reasoning",
    )
    verdict = validate_decomposition_proposal(proposal)
    assert verdict.decision == "REJECT"
    assert any("exceeds parent" in r for r in verdict.reasons)


def test_authority_equal_or_lower_than_parent_allowed():
    proposal = _proposal(
        [ChildProposal(semantic_key="c1", role="elis-ideas", purpose="a", authority_class="cognitive_reasoning")],
        parent_authority_class="orchestration_decision",
    )
    verdict = validate_decomposition_proposal(proposal)
    assert verdict.decision == "AUTHORIZE"


def test_illegal_dependency_on_nonexistent_sibling_rejected():
    proposal = _proposal([ChildProposal(semantic_key="c1", role="elis-ideas", purpose="a", dependencies=("ghost",))])
    verdict = validate_decomposition_proposal(proposal)
    assert verdict.decision == "REJECT"
    assert any("illegal dependency" in r for r in verdict.reasons)


def test_self_dependency_rejected():
    proposal = _proposal([ChildProposal(semantic_key="c1", role="elis-ideas", purpose="a", dependencies=("c1",))])
    verdict = validate_decomposition_proposal(proposal)
    assert verdict.decision == "REJECT"
    assert any("cannot depend on itself" in r for r in verdict.reasons)


def test_legal_sibling_dependency_allowed():
    proposal = _proposal(
        [
            ChildProposal(semantic_key="c1", role="elis-ideas", purpose="a"),
            ChildProposal(semantic_key="c2", role="elis-ideas", purpose="b", dependencies=("c1",)),
        ]
    )
    verdict = validate_decomposition_proposal(proposal)
    assert verdict.decision == "AUTHORIZE"


def test_empty_decomposition_rejected():
    proposal = _proposal([])
    verdict = validate_decomposition_proposal(proposal)
    assert verdict.decision == "REJECT"


def test_bounded_topology_limit_enforced():
    children = [ChildProposal(semantic_key=f"c{i}", role="elis-ideas", purpose="a") for i in range(MAX_CHILDREN_PER_PROPOSAL + 1)]
    proposal = _proposal(children)
    verdict = validate_decomposition_proposal(proposal)
    assert verdict.decision == "REJECT"
    assert any("exceeds bounded topology limit" in r for r in verdict.reasons)


def test_at_limit_topology_allowed():
    children = [ChildProposal(semantic_key=f"c{i}", role="elis-ideas", purpose="a") for i in range(MAX_CHILDREN_PER_PROPOSAL)]
    proposal = _proposal(children)
    verdict = validate_decomposition_proposal(proposal)
    assert verdict.decision == "AUTHORIZE"


def test_decomposition_partial_invalidity_rejects_whole_proposal():
    """One invalid child among several valid ones rejects the WHOLE
    proposal, not just the bad child -- prevents an LLM from 'fishing' for
    which children get silently authorized."""
    proposal = _proposal(
        [
            ChildProposal(semantic_key="good", role="elis-ideas", purpose="a"),
            ChildProposal(semantic_key="bad", role="not-a-real-profile", purpose="b"),
        ]
    )
    verdict = validate_decomposition_proposal(proposal)
    assert verdict.decision == "REJECT"
