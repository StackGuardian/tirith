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
    # Additional tests to cover previously uncovered lines
    (
        "items.*.data.value",
        {
            "items": [
                {"data": {"value": "foo"}},
                {"data": {"value": "bar"}},
                {"data": {"other": "baz"}},
                {},
            ]
        },
        ["foo", "bar", None, None],
    ),
    (
        "records.*.info",
        {
            "records": [
                {"info": "x"},
                {"info": "y"},
                {},
            ]
        },
        ["x", "y", None],
    ),
]


# pytest -v -m passing
@mark.passing
@mark.parametrize("split_expressions,input_data,expected_result", checks_passing)
def test_(split_expressions, input_data, expected_result):
    result = handler._wrapper_get_exp_attribute(split_expressions, input_data)
    assert result == expected_result


def load_json_from_fixtures(json_path):
    current_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_path, "fixtures", json_path)) as f:
        return json.load(f)


def test_multiple_resource_tag_check():
    input_data = load_json_from_fixtures("input_multiple_resource_tag_check.json")
    policy = load_json_from_fixtures("policy_multiple_resource_tag_check.json")
    result = start_policy_evaluation_from_dict(policy, input_data)

    assert result["final_result"] is False
    assert len(result["evaluators"][0]["result"]) > 1
    has_passed = any(item.get("passed") is True for item in result["evaluators"][0]["result"])
    has_failed = any(item.get("passed") is False for item in result["evaluators"][0]["result"])
    assert has_passed and has_failed, "Should have both passing and failing resource evaluations"


def test_multiple_resource_tag_check_all_resources_have_tag():
    input_data = load_json_from_fixtures("input_multiple_resource_tag_check.json")

    for resource in input_data.get("resource_changes", []):
        if "tags" not in resource.get("change", {}).get("after", {}) or resource["change"]["after"]["tags"] is None:
            resource["change"]["after"]["tags"] = {"a": "true"}

    policy = load_json_from_fixtures("policy_multiple_resource_tag_check.json")
    result = start_policy_evaluation_from_dict(policy, input_data)

    assert result["final_result"] is True
    all_passed = all(item.get("passed") is True for item in result["evaluators"][0]["result"])
    assert all_passed, "All resource evaluations should pass when all have the required tag"


def test_star_with_not_found_attribute_should_raise_providererror():
    input_data = load_json_from_fixtures("input_costcenter_tags.json")
    policy = load_json_from_fixtures("policy_star_restype_should_skip.json")

    result = start_policy_evaluation_from_dict(policy, input_data)

    # The policy tries to access 'shouldnt_exist' attribute on all resources (*)
    # Since this attribute doesn't exist, it should return ProviderError
    # With error_tolerance=2, errors with severity <= 2 should be skipped

    # Check that we have results for multiple resources
    assert len(result["evaluators"][0]["result"]) == 3

    # All results should have ProviderError values (skipped due to error tolerance)
    for item in result["evaluators"][0]["result"]:
        # With error_tolerance=2, provider errors should be skipped (passed=None)
        assert item.get("passed") is None
        # The message should indicate the attribute was not found
        assert "shouldnt_exist" in item.get("message", "")
