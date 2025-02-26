# Maintain all core related tests here
from pytest import mark

from tirith.core.core import final_evaluator
from tirith.core.core import start_policy_evaluation_from_dict

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


@mark.passing
def test_start_policy_evaluation_with_required_provider():
    policy_dict = {
        "meta": {"version": "1.0", "required_provider": "legacy_provider"},
        "evaluators": [],
        "eval_expression": "True",
    }
    input_dict = {}
    
    result = start_policy_evaluation_from_dict(policy_dict, input_dict)
    
    assert result["meta"]["provider"] == "legacy_provider"

@mark.passing
def test_start_policy_evaluation_with_provider():
    policy_dict = {
        "meta": {"version": "1.0", "provider": "new_provider"},
        "evaluators": [],
        "eval_expression": "True",
    }
    input_dict = {}
    
    result = start_policy_evaluation_from_dict(policy_dict, input_dict)
    
    assert result["meta"]["provider"] == "new_provider"

@mark.passing
def test_start_policy_evaluation_with_both_providers():
    policy_dict = {
        "meta": {"version": "1.0", "provider": "new_provider", "required_provider": "legacy_provider"},
        "evaluators": [],
        "eval_expression": "True",
    }
    input_dict = {}
    
    result = start_policy_evaluation_from_dict(policy_dict, input_dict)
    
    assert result["meta"]["provider"] == "new_provider"

@mark.passing
def test_start_policy_evaluation_with_neither_provider():
    policy_dict = {
        "meta": {"version": "1.0"},
        "evaluators": [],
        "eval_expression": "True",
    }
    input_dict = {}
    
    result = start_policy_evaluation_from_dict(policy_dict, input_dict)
    
    assert result["meta"]["provider"] == "core"