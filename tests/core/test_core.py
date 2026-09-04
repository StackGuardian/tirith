# Maintain all core related tests here
from pytest import mark
import pytest

from tirith.core.core import final_evaluator, generate_evaluator_result
from tirith.providers.common import ProviderError
from unittest.mock import patch, MagicMock


@mark.passing
def test_final_evaluator_skipped_check_should_be_removed():
    actual_result = final_evaluator("!skipped_check && passing_check", dict(skipped_check=None, passing_check=True))
    assert actual_result == (True, [])

    actual_result = final_evaluator("!skipped_check && passing_check", dict(skipped_check=None, passing_check=False))
    assert actual_result == (False, [])


@mark.passing
def test_final_evaluator_undef_var_should_be_removed_from_exp():
    actual_result = final_evaluator(
        "!skipped_check && passing_check || undefined_check", dict(skipped_check=None, passing_check=True)
    )
    assert actual_result == (
        True,
        ["The following evaluator ids are not defined and have been removed: undefined_check"],
    )

    actual_result = final_evaluator(
        "!skipped_check && passing_check || undefined_check", dict(skipped_check=None, passing_check=False)
    )
    assert actual_result == (
        False,
        ["The following evaluator ids are not defined and have been removed: undefined_check"],
    )


@mark.passing
def test_final_evaluator_malicious_eval_should_err():
    actual_result = final_evaluator(
        "!skipped_check && passing_check || [].__class__.__base__", dict(skipped_check=None, passing_check=True)
    )
    assert actual_result == (False, ["The following symbols are not allowed: __class__, __base__"])


class MockEvaluator:
    def evaluate(self, input_value, data):
        if input_value == "resource1":
            return {"passed": True, "message": "First resource passed"}
        else:
            return {"passed": False, "message": "Second resource failed"}


@mark.passing
def test_generate_evaluator_result_empty_inputs():
    """Test that when a provider returns no inputs, the evaluation should fail."""
    # Mock evaluator object
    evaluator_obj = {
        "id": "test_evaluator",
        "provider_args": {"operation_type": "attribute", "key": "value"},
        "condition": {"type": "Equals", "value": True},
    }

    # Mock the provider function to return empty list
    with patch("tirith.core.core.get_evaluator_inputs_from_provider_inputs", return_value=[]):
        result = generate_evaluator_result(evaluator_obj, {}, "test_provider")

        # Verify the result shows a failed evaluation with the correct message
        assert result["passed"] is False
        assert len(result["result"]) == 1
        assert result["result"][0]["passed"] is False
        assert result["result"][0]["message"] == "Could not find input value for operation_type: 'attribute'"


@mark.passing
def test_generate_evaluator_result_provider_error_above_tolerance():
    """Test that provider errors with severity higher than tolerance cause the evaluation to fail."""
    # Mock evaluator object with error_tolerance = 1
    evaluator_obj = {
        "id": "test_evaluator",
        "provider_args": {"operation_type": "attribute", "key": "value"},
        "condition": {"type": "Equals", "value": True, "error_tolerance": 1},
    }

    # Create a provider error with severity 2 (above tolerance)
    provider_error = {"value": ProviderError(severity_value=2), "err": "Resource not found"}

    # Mock the provider function to return the error
    with patch("tirith.core.core.get_evaluator_inputs_from_provider_inputs", return_value=[provider_error]):
        # Create a mapping for EVALUATORS_DICT.get to return a mock evaluator class
        mock_evaluator_dict = {"Equals": MockEvaluator}
        with patch("tirith.core.core.EVALUATORS_DICT", mock_evaluator_dict):
            result = generate_evaluator_result(evaluator_obj, {}, "test_provider")

            # Verify the result shows a failed evaluation
            assert result["passed"] is False
            assert len(result["result"]) == 1
            assert result["result"][0]["passed"] is False
            assert result["result"][0]["message"] == "Resource not found"


@mark.passing
def test_generate_evaluator_result_provider_error_within_tolerance():
    """Test that provider errors with severity within tolerance are skipped."""
    # Mock evaluator object with error_tolerance = 2
    evaluator_obj = {
        "id": "test_evaluator",
        "provider_args": {"operation_type": "attribute", "key": "value"},
        "condition": {"type": "Equals", "value": True, "error_tolerance": 2},
    }

    # Create a provider error with severity 1 (within tolerance)
    provider_error = {"value": ProviderError(severity_value=1), "err": "Minor issue"}

    # Mock the provider function to return the error
    with patch("tirith.core.core.get_evaluator_inputs_from_provider_inputs", return_value=[provider_error]):
        # Create a mapping for EVALUATORS_DICT.get to return a mock evaluator class
        mock_evaluator_dict = {"Equals": MockEvaluator}
        with patch("tirith.core.core.EVALUATORS_DICT", mock_evaluator_dict):
            result = generate_evaluator_result(evaluator_obj, {}, "test_provider")

            # Verify the result shows a skipped evaluation
            assert result["passed"] is None
            assert len(result["result"]) == 1
            assert result["result"][0]["passed"] is None
            assert result["result"][0]["message"] == "Minor issue"


@mark.passing
def test_generate_evaluator_result_multiple_resources_one_failing():
    """Test that when one resource fails, the entire evaluation fails."""
    # Mock evaluator object
    evaluator_obj = {
        "id": "test_evaluator",
        "provider_args": {"operation_type": "attribute", "key": "value"},
        "condition": {"type": "Equals", "value": "expected_value"},
    }

    # Mock provider to return two resources
    with patch(
        "tirith.core.core.get_evaluator_inputs_from_provider_inputs",
        return_value=[{"value": "resource1"}, {"value": "resource2"}],
    ):
        # Create a mapping for EVALUATORS_DICT.get to return our mock evaluator class
        mock_evaluator_dict = {"Equals": MockEvaluator}
        with patch("tirith.core.core.EVALUATORS_DICT", mock_evaluator_dict):
            result = generate_evaluator_result(evaluator_obj, {}, "test_provider")

            # Verify the result shows a failed evaluation even though one resource passed
            assert result["passed"] is False
            assert len(result["result"]) == 2
            assert result["result"][0]["passed"] is True
            assert result["result"][1]["passed"] is False


@mark.passing
def test_generate_evaluator_result_unsupported_evaluator_populates_result():
    """
    An unsupported condition.type must still produce a "result" list. Consumers index into
    it unconditionally, so an early return without it used to raise KeyError far from the cause.
    """
    evaluator_obj = {
        "id": "test_evaluator",
        "provider_args": {"operation_type": "attribute", "key": "value"},
        "condition": {"type": "NotAnEvaluator", "value": True},
    }

    with patch("tirith.core.core.get_evaluator_inputs_from_provider_inputs", return_value=[{"value": "x"}]):
        result = generate_evaluator_result(evaluator_obj, {}, "test_provider")

    assert result["passed"] is False
    assert result["result"] == [{"passed": False, "message": "`NotAnEvaluator` is not a supported evaluator"}]


@mark.passing
def test_generate_evaluator_result_bare_provider_err_is_surfaced():
    """
    A provider that reports "err" without a ProviderError is a malformed provider call (bad
    operation_type, missing arg), not a policy violation. The message must reach the output
    instead of being dropped and None evaluated against the condition.
    """
    evaluator_obj = {
        "id": "test_evaluator",
        "provider_args": {"operation_type": "gt_value", "key": "value"},
        "condition": {"type": "Equals", "value": "us-east-1"},
    }

    bare_err = {"value": None, "meta": None, "err": "operation_type: gt_value is not supported"}

    with patch("tirith.core.core.get_evaluator_inputs_from_provider_inputs", return_value=[bare_err]):
        with patch("tirith.core.core.EVALUATORS_DICT", {"Equals": MockEvaluator}):
            result = generate_evaluator_result(evaluator_obj, {}, "test_provider")

    assert result["passed"] is False
    assert len(result["result"]) == 1
    assert result["result"][0]["passed"] is False
    assert result["result"][0]["message"] == "operation_type: gt_value is not supported"


@mark.passing
def test_generate_evaluator_result_bare_provider_err_ignores_error_tolerance():
    """error_tolerance tolerates missing data; it must never mask a malformed provider call."""
    evaluator_obj = {
        "id": "test_evaluator",
        "provider_args": {"operation_type": "gt_value", "key": "value"},
        # A tolerance high enough to swallow every documented severity, including 99.
        "condition": {"type": "Equals", "value": "us-east-1", "error_tolerance": 100},
    }

    bare_err = {"value": None, "meta": None, "err": "operation_type: gt_value is not supported"}

    with patch("tirith.core.core.get_evaluator_inputs_from_provider_inputs", return_value=[bare_err]):
        with patch("tirith.core.core.EVALUATORS_DICT", {"Equals": MockEvaluator}):
            result = generate_evaluator_result(evaluator_obj, {}, "test_provider")

    assert result["passed"] is False, "a malformed provider call must not be skipped"
    assert result["result"][0]["passed"] is False


def _skip(msg="tolerated"):
    return {"value": ProviderError(severity_value=0), "err": msg}


def _rollup(inputs, error_tolerance=0):
    """Run generate_evaluator_result over `inputs` with MockEvaluator and return the verdict."""
    evaluator_obj = {
        "id": "test_evaluator",
        "provider_args": {"operation_type": "attribute", "key": "value"},
        "condition": {"type": "Equals", "value": "expected_value", "error_tolerance": error_tolerance},
    }
    with patch("tirith.core.core.get_evaluator_inputs_from_provider_inputs", return_value=inputs):
        with patch("tirith.core.core.EVALUATORS_DICT", {"Equals": MockEvaluator}):
            return generate_evaluator_result(evaluator_obj, {}, "test_provider")


@mark.passing
@pytest.mark.parametrize(
    "inputs",
    [
        [{"value": "resource2"}, _skip()],  # violation first, then a tolerated skip (issue #293)
        [_skip(), {"value": "resource2"}],  # the same two resources, swapped
    ],
    ids=["fail-then-skip", "skip-then-fail"],
)
def test_generate_evaluator_result_skip_never_erases_a_failure(inputs):
    """A tolerated skip must not turn a failing evaluator into a skipped one, whatever the order.

    Regression for #293: a destroyed resource (severity 0, tolerated at every error_tolerance)
    after a violating resource used to reset the verdict to None, and the None id was then removed
    from eval_expression, so the violation vanished.
    """
    result = _rollup(inputs)
    assert result["passed"] is False
    assert sorted((r["passed"] for r in result["result"]), key=str) == [False, None]


@mark.passing
@pytest.mark.parametrize(
    "inputs",
    [
        [{"value": "resource1"}, _skip()],
        [_skip(), {"value": "resource1"}],
        [{"value": "resource1"}, _skip(), {"value": "resource1"}],
    ],
    ids=["pass-then-skip", "skip-then-pass", "pass-skip-pass"],
)
def test_generate_evaluator_result_skip_never_erases_a_pass(inputs):
    """A skipped resource alongside passing ones leaves a passing verdict, not a skipped one.

    Before #293 was fixed, [PASS, skip] reported "Passed: 0 Failed: 0 Skipped: 1" and exited 1 for a
    plan that had a compliant resource next to a destroyed one.
    """
    result = _rollup(inputs)
    assert result["passed"] is True


@mark.passing
def test_generate_evaluator_result_all_skipped_is_none():
    """Only when every resource was tolerated away is the evaluator skipped as a whole."""
    result = _rollup([_skip(), _skip()])
    assert result["passed"] is None
    assert all(r["passed"] is None for r in result["result"])


@mark.passing
def test_generate_evaluator_result_skip_never_erases_a_bare_provider_error():
    """A malformed provider call fails hard even when a tolerated skip follows it."""
    result = _rollup([{"value": None, "err": "attribute_to_get is not supported"}, _skip()])
    assert result["passed"] is False
