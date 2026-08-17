from __future__ import annotations

import pytest
from temporalio.common import WorkflowIDReusePolicy

from elis_temporal.policies.workflow_identity import (
    InvalidWorkflowIdentityComponent,
    SemanticWorkflowId,
    build_semantic_workflow_id,
    id_reuse_policy_for_intent,
)


def test_build_semantic_workflow_id_shape():
    wid = build_semantic_workflow_id("core", "gated-pipeline", "t_76bf11e1")
    assert wid == "ELIS/core/gated-pipeline/t_76bf11e1"


def test_same_semantic_key_same_id_duplicate_retry():
    """(test ledger item 1) Two calls with identical (domain, process,
    semantic_key) -- e.g. a retry of the same logical work -- must produce
    the exact same Workflow ID string, so Temporal's own ID uniqueness
    handles dedup rather than a second ELIS-side mechanism."""
    a = build_semantic_workflow_id("core", "gated-pipeline", "t_76bf11e1")
    b = build_semantic_workflow_id("core", "gated-pipeline", "t_76bf11e1")
    assert a == b


def test_distinct_semantic_key_distinct_id():
    """(test ledger item 2) Genuinely distinct work (different semantic
    key) must never collapse onto the same Workflow ID."""
    a = build_semantic_workflow_id("core", "gated-pipeline", "t_76bf11e1")
    b = build_semantic_workflow_id("core", "gated-pipeline", "t_aad1b908")
    assert a != b


def test_distinct_domain_or_process_also_distinguishes():
    same_key_diff_domain = build_semantic_workflow_id("research", "gated-pipeline", "t_x")
    same_key_diff_process = build_semantic_workflow_id("core", "profile-lock", "t_x")
    same_key_core = build_semantic_workflow_id("core", "gated-pipeline", "t_x")
    assert len({same_key_diff_domain, same_key_diff_process, same_key_core}) == 3


@pytest.mark.parametrize("intent", ["initial", "retry", "distinct"])
def test_reuse_policy_is_failed_only_never_blind_allow_duplicate(intent):
    """No intent maps to plain ALLOW_DUPLICATE -- that would let a second
    concurrent start against a still-running or already-succeeded ID
    through, which is exactly the duplicate-logical-execution failure mode
    this scheme exists to prevent."""
    policy = id_reuse_policy_for_intent(intent)
    assert policy == WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY


def test_unknown_intent_rejected():
    with pytest.raises(ValueError):
        id_reuse_policy_for_intent("correction")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "domain,process,semantic_key",
    [
        ("", "gated-pipeline", "t_x"),
        ("core", "", "t_x"),
        ("core", "gated-pipeline", ""),
        ("co/re", "gated-pipeline", "t_x"),
        ("core", "gated pipeline", "t_x"),
    ],
)
def test_invalid_components_rejected(domain, process, semantic_key):
    with pytest.raises(InvalidWorkflowIdentityComponent):
        SemanticWorkflowId(domain=domain, process=process, semantic_key=semantic_key)
