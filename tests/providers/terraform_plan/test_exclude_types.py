import pytest
from tirith.providers.terraform_plan import handler
from tirith.core.core import start_policy_evaluation_from_dict
import json
import os


def load_json_from_fixtures(json_path):
    current_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_path, "fixtures", json_path)) as f:
        return json.load(f)


def test_exclude_types_attribute():
    """Test that resources with types in exclude_types are skipped when using wildcard"""
    input_data = load_json_from_fixtures("input_exclude_types.json")

    # Test with exclude_types
    provider_args = {
        "operation_type": "attribute",
        "terraform_resource_type": "*",
        "terraform_resource_attribute": "tags",
        "exclude_types": ["aws_iam_role_policy_attachment"],
    }

    result = handler.provide(provider_args, input_data)

    # Verify that we get results for aws_iam_role and aws_instance but not for aws_iam_role_policy_attachment
    resource_types = set()
    for item in result:
        if "meta" in item and "type" in item["meta"]:
            resource_types.add(item["meta"]["type"])

    assert "aws_iam_role" in resource_types
    assert "aws_instance" in resource_types
    assert "aws_iam_role_policy_attachment" not in resource_types


def test_exclude_types_action():
    """Test that resources with types in exclude_types are skipped when using wildcard for action operation"""
    input_data = load_json_from_fixtures("input_exclude_types.json")

    # Test with exclude_types
    provider_args = {
        "operation_type": "action",
        "terraform_resource_type": "*",
        "exclude_types": ["aws_iam_role_policy_attachment"],
    }

    result = handler.provide(provider_args, input_data)

    # Verify that we get results for aws_iam_role and aws_instance but not for aws_iam_role_policy_attachment
    resource_types = set()
    for item in result:
        if "meta" in item and "type" in item["meta"]:
            resource_types.add(item["meta"]["type"])

    assert "aws_iam_role" in resource_types
    assert "aws_instance" in resource_types
    assert "aws_iam_role_policy_attachment" not in resource_types


def test_exclude_types_count():
    """Test that resources with types in exclude_types are skipped when using wildcard for count operation"""
    input_data = load_json_from_fixtures("input_exclude_types.json")

    # First, count all resources
    provider_args_all = {"operation_type": "count", "terraform_resource_type": "*"}

    result_all = handler.provide(provider_args_all, input_data)
    total_count = result_all[0]["value"]

    # Now count with exclusion
    provider_args_exclude = {
        "operation_type": "count",
        "terraform_resource_type": "*",
        "exclude_types": ["aws_iam_role_policy_attachment"],
    }

    result_exclude = handler.provide(provider_args_exclude, input_data)
    exclude_count = result_exclude[0]["value"]

    # Verify that the count is reduced by the number of excluded resources
    assert exclude_count < total_count

    # Count only the excluded type to verify the difference
    provider_args_only_excluded = {
        "operation_type": "count",
        "terraform_resource_type": "aws_iam_role_policy_attachment",
    }

    result_only_excluded = handler.provide(provider_args_only_excluded, input_data)
    excluded_type_count = result_only_excluded[0]["value"]

    assert total_count - exclude_count == excluded_type_count


def test_policy_exclude_types():
    """Test that the policy evaluation works correctly with exclude_types"""
    input_data = load_json_from_fixtures("input_exclude_types.json")
    policy = load_json_from_fixtures("policy_exclude_types.json")

    result = start_policy_evaluation_from_dict(policy, input_data)

    # The policy should pass if aws_iam_role_policy_attachment resources are excluded
    # and all other resources have tags
    assert result["final_result"] is True
