from __future__ import annotations

import pytest

from elis_temporal.workflows.gated_pipeline_workflow import SelfValidationError, assert_no_self_validation


def test_different_profiles_pass():
    assert_no_self_validation("elis-pm", "elis-advisor")  # no raise


def test_same_profile_raises():
    """(test ledger item 8, gated-pipeline half -- decomposition-time
    self-validation is covered separately in test_decomposition.py)."""
    with pytest.raises(SelfValidationError):
        assert_no_self_validation("elis-pm", "elis-pm")
