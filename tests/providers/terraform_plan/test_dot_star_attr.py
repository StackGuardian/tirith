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
    # Test case for intermediate ".*" expression handling
    (
        "resource.*.tags.application_acronym",
        {
            "resource": [
                {"tags": {"application_acronym": "ABC", "other": "tag1"}},
                {"tags": {"application_acronym": "DEF", "other": "tag2"}},
                {"tags": {"other": "tag3"}},  # Missing application_acronym
                {"other_field": "no_tags"},  # Missing tags entirely
            ]
        },
        ["ABC", "DEF", None, None],
    ),
]


# pytest -v -m passing
@mark.passing
@mark.parametrize("split_expressions,input_data,expected_result", checks_passing)
def test_(split_expressions, input_data, expected_result):
    result = handler._wrapper_get_exp_attribute(split_expressions, input_data)
    assert result == expected_result


# Test for intermediate ".*" expression with real Terraform structure
def test_intermediate_dot_star_expression():
    """
    Test specifically for the intermediate ".*" expression handling where
    an attribute path contains dot-star in the middle and needs to
    extract values from a list of objects, properly handling cases where
    the path after the dot-star exists or doesn't exist.
    """
    # Data structure similar to terraform ebs_block_device structure
    terraform_data = {
        "ebs_block_device": [
            {"device_name": "/dev/sdf", "tags": {"Name": "EBS-1"}},
            {"device_name": "/dev/sdg", "tags": {"Name": "EBS-2", "application_acronym": "XYZ"}},
            {"device_name": "/dev/sdh", "tags": {"application_acronym": "ABC"}},
            {"device_name": "/dev/sdi", "volume_size": 20},  # No tags field
        ]
    }

    # This expression should test the intermediate_exp[1].lstrip(".") code path
    expression = "ebs_block_device.*.tags.application_acronym"
    result = handler._wrapper_get_exp_attribute(expression, terraform_data)

    # Should have values for items with application_acronym and None for those without
    expected = [None, "XYZ", "ABC", None]
    assert result == expected, f"Expected {expected}, got {result}"


# Load AWS instance EBS test case from fixture
def test_aws_instance_ebs_block_device_tags():
    """
    Test using the AWS instance EBS fixture to verify the handling of
    ebs_block_device.*.tags.application_acronym in a real Terraform plan.
    """
    # Load the input fixture
    current_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_path, "fixtures", "input_aws_instance_ebs.json")) as f:
        input_data = json.load(f)

    # Load the policy
    with open(os.path.join(current_path, "fixtures", "policy_aws_instance_ebs.json")) as f:
        policy = json.load(f)

    # Run the policy evaluation
    result = start_policy_evaluation_from_dict(policy, input_data)

    # The policy should fail because one EBS block device is missing the application_acronym tag
    assert result["final_result"] is False

    # Check the individual evaluator results
    # First evaluator checks tags.application_acronym on all resources (should pass)
    assert result["evaluators"][0]["result"][0]["passed"] is True

    # Second evaluator checks ebs_block_device.*.tags.application_acronym (should fail)
    assert result["evaluators"][1]["result"][0]["passed"] is False

    # Verify that we get the correct values in ebs_block_device.*.tags.application_acronym
    # The first EBS block has no application_acronym tag
    resource_values = input_data["resource_changes"][0]["change"]["after"]
    input_resource_change_attrs = resource_values

    attribute = "ebs_block_device.*.tags.application_acronym"
    result = handler._wrapper_get_exp_attribute(attribute, input_resource_change_attrs)

    # Should match the EBS blocks: first one has no tag, second and third have "TTO"
    expected = [None, "TTO", "TTO"]
    assert result == expected, f"Expected {expected}, got {result}"


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
