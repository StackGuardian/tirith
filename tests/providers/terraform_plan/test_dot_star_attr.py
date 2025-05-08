from tirith.providers.terraform_plan import handler
from pytest import mark
from tirith.core.core import start_policy_evaluation_from_dict
import json
import os
import pytest

checks_passing = [
    (
        "a.*.b.c.*",
        {
            "a": [
                {"b": {"c": ["val1", "val3"]}},
                {"b": {"c": ["val8", "val4"]}},
                {"b": {"c": ["val9", "val5"]}},
                {"d": {"c": ["val10", "val6"]}},
                {"b": {"f": ["val11", "val7"]}},
            ]
        },
        ["val1", "val3", "val8", "val4", "val9", "val5", None, None],
    ),
    (
        "a.*.b.c",
        {
            "a": [
                {"b": {"c": ["val1", "val3"]}},
                {"b": {"c": ["val8", "val4"]}},
                {"b": {"c": ["val9", "val5"]}},
                {"d": {"c": ["val10", "val6"]}},
                {"b": {"f": ["val11", "val7"]}},
            ]
        },
        [["val1", "val3"], ["val8", "val4"], ["val9", "val5"], None, None],
    ),
    (
        "a.b.c",
        {"a": {"b": {"c": ["val1", "val3"]}}},
        [["val1", "val3"]],
    ),
    (
        "a.*.b",
        {
            "a": [
                {"b": {"c": ["val1", "val3"]}},
                {"b": {"c": ["val8", "val4"]}},
                {"b": {"c": ["val9", "val5"]}},
                {"d": {"c": ["val10", "val6"]}},
                {"b": {"f": ["val11", "val7"]}},
            ]
        },
        [{"c": ["val1", "val3"]}, {"c": ["val8", "val4"]}, {"c": ["val9", "val5"]}, None, {"f": ["val11", "val7"]}],
    ),
]


# pytest -v -m passing
@mark.passing
@mark.parametrize("split_expressions,input_data,expected_result", checks_passing)
def test_(split_expressions, input_data, expected_result):
    result = handler._wrapper_get_exp_attribute(split_expressions, input_data)
    assert result == expected_result


# Tests for multiple resource tag check
def load_json_from_fixtures(json_path):
    current_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_path, "fixtures", json_path)) as f:
        return json.load(f)


def test_multiple_resource_tag_check():
    """
    Test that policy evaluation correctly checks tags across multiple resources.
    This verifies the fix for the bug where resources without the requested tag
    were being omitted from evaluation.
    """
    # Load the input fixture with multiple resources (some with tags, some without)
    input_data = load_json_from_fixtures("input_multiple_resource_tag_check.json")

    # Load the policy that should check for a specific tag across all resources
    policy = load_json_from_fixtures("policy_multiple_resource_tag_check.json")

    # Run the policy evaluation
    result = start_policy_evaluation_from_dict(policy, input_data)

    # Verify that the policy fails (as expected) because some resources don't have the tag
    assert result["final_result"] is False

    # Verify that all resources were evaluated (not just the ones with the tag)
    assert len(result["evaluators"][0]["result"]) > 1

    # Verify that we have both successful and failed evaluations
    has_passed = any(item.get("passed") is True for item in result["evaluators"][0]["result"])
    has_failed = any(item.get("passed") is False for item in result["evaluators"][0]["result"])

    # We expect to have both resources with and without the tag
    assert has_passed and has_failed, "Should have both passing and failing resource evaluations"


def test_multiple_resource_tag_check_all_resources_have_tag():
    """
    Test that when all resources have the required tag, the policy passes.
    This validates the fix ensures correct passing behavior too.
    """
    # Load the input fixture with multiple resources
    input_data = load_json_from_fixtures("input_multiple_resource_tag_check.json")

    # Modify all resources to have the required tag
    for resource in input_data.get("resource_changes", []):
        if "tags" not in resource.get("change", {}).get("after", {}) or resource["change"]["after"]["tags"] is None:
            resource["change"]["after"]["tags"] = {"a": "true"}

    # Load the policy that checks for a specific tag across all resources
    policy = load_json_from_fixtures("policy_multiple_resource_tag_check.json")

    # Run the policy evaluation
    result = start_policy_evaluation_from_dict(policy, input_data)

    # Verify that the policy passes because all resources now have the tag
    assert result["final_result"] is True

    # Verify that all evaluations passed
    all_passed = all(item.get("passed") is True for item in result["evaluators"][0]["result"])
    assert all_passed, "All resource evaluations should pass when all have the required tag"
