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
        "condition": {"type": "Equals", "value": True}
    }
    
    # Mock the provider function to return empty list
    with patch('tirith.core.core.get_evaluator_inputs_from_provider_inputs', return_value=[]):
        result = generate_evaluator_result(evaluator_obj, {}, "test_provider")
        
        # Verify the result shows a failed evaluation with the correct message
        assert result["passed"] is False
        assert len(result["result"]) == 1
        assert result["result"][0]["passed"] is False
        assert result["result"][0]["message"] == "Could not find input value"


@mark.passing
def test_generate_evaluator_result_provider_error_above_tolerance():
    """Test that provider errors with severity higher than tolerance cause the evaluation to fail."""
    # Mock evaluator object with error_tolerance = 1
    evaluator_obj = {
        "id": "test_evaluator",
        "provider_args": {"operation_type": "attribute", "key": "value"},
        "condition": {"type": "Equals", "value": True, "error_tolerance": 1}
    }
    
    # Create a provider error with severity 2 (above tolerance)
    provider_error = {"value": ProviderError(severity_value=2), "err": "Resource not found"}
    
    # Mock the provider function to return the error
    with patch('tirith.core.core.get_evaluator_inputs_from_provider_inputs', return_value=[provider_error]):
        # Create a mapping for EVALUATORS_DICT.get to return a mock evaluator class
        mock_evaluator_dict = {"Equals": MockEvaluator}
        with patch('tirith.core.core.EVALUATORS_DICT', mock_evaluator_dict):
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
        "condition": {"type": "Equals", "value": True, "error_tolerance": 2}
    }
    
    # Create a provider error with severity 1 (within tolerance)
    provider_error = {"value": ProviderError(severity_value=1), "err": "Minor issue"}
    
    # Mock the provider function to return the error
    with patch('tirith.core.core.get_evaluator_inputs_from_provider_inputs', return_value=[provider_error]):
        # Create a mapping for EVALUATORS_DICT.get to return a mock evaluator class
        mock_evaluator_dict = {"Equals": MockEvaluator}
        with patch('tirith.core.core.EVALUATORS_DICT', mock_evaluator_dict):
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
        "condition": {"type": "Equals", "value": "expected_value"}
    }
    
    # Mock provider to return two resources
    with patch('tirith.core.core.get_evaluator_inputs_from_provider_inputs', 
               return_value=[{"value": "resource1"}, {"value": "resource2"}]):
        # Create a mapping for EVALUATORS_DICT.get to return our mock evaluator class
        mock_evaluator_dict = {"Equals": MockEvaluator}
        with patch('tirith.core.core.EVALUATORS_DICT', mock_evaluator_dict):
            result = generate_evaluator_result(evaluator_obj, {}, "test_provider")
            
            # Verify the result shows a failed evaluation even though one resource passed
            assert result["passed"] is False
            assert len(result["result"]) == 2
            assert result["result"][0]["passed"] is True
            assert result["result"][1]["passed"] is False
