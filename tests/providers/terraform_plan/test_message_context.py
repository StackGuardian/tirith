"""
Tests for the resource context that the terraform_plan provider attaches to its results.

Without it a message only states the comparison that was made, which reads the same for every
resource in a plan. These tests pin the resource address, the planned action and the attribute
into the message, and the same detail into the `context` of the result document.
"""

import json
import os

from pytest import mark

from tirith.core.core import start_policy_evaluation_from_dict
from tirith.providers.terraform_plan import handler
from utils import load_terraform_plan_json


def load_policy_from_fixtures(json_path):
    current_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_path, "fixtures", json_path)) as f:
        return json.load(f)


def evaluate(input_json, policy_json):
    return start_policy_evaluation_from_dict(
        load_policy_from_fixtures(policy_json), load_terraform_plan_json(input_json)
    )


def evaluate_provider_args(provider_args, condition, input_json):
    """Evaluate a single set of provider args, so a test does not need a policy fixture."""
    policy = {
        "meta": {"version": "v1", "required_provider": "stackguardian/terraform_plan"},
        "evaluators": [{"id": "check", "provider_args": provider_args, "condition": condition}],
        "eval_expression": "check",
    }
    return start_policy_evaluation_from_dict(policy, load_terraform_plan_json(input_json))


def messages_of(result, evaluator_index=0):
    return [item["message"] for item in result["evaluators"][evaluator_index]["result"]]


def contexts_of(result, evaluator_index=0):
    return [item.get("context") for item in result["evaluators"][evaluator_index]["result"]]


@mark.passing
def test_attribute_message_names_the_resource_the_action_and_the_attribute():
    result = evaluate("input_multiple_resource_tag_check.json", "policy_multiple_resource_tag_check.json")

    assert messages_of(result) == [
        '[aws_s3_bucket.bucket_with_tag (create)] tags.a: `"true"` is not empty',
        "[aws_s3_bucket.bucket_without_tag (create)] attribute: 'tags.a' is not found",
    ]


@mark.passing
def test_attribute_context_carries_the_same_detail_as_the_message():
    result = evaluate("input_multiple_resource_tag_check.json", "policy_multiple_resource_tag_check.json")

    assert contexts_of(result) == [
        {
            "operation_type": "attribute",
            "resource_type": "aws_s3_bucket",
            "resource_address": "aws_s3_bucket.bucket_with_tag",
            "action": "create",
            "attribute": "tags.a",
        },
        {
            "operation_type": "attribute",
            "resource_type": "aws_s3_bucket",
            "resource_address": "aws_s3_bucket.bucket_without_tag",
            "action": "create",
        },
    ]


@mark.passing
def test_wildcard_attribute_reports_the_index_it_resolved_to():
    # Every result of `ebs_block_device.*.tags.application_acronym` used to read identically,
    # so there was no way to tell which block device was the one missing its tag
    result = evaluate("input_aws_instance_ebs.json", "policy_aws_instance_ebs.json")

    assert messages_of(result, evaluator_index=1) == [
        "[aws_instance.example (create)] ebs_block_device.0.tags.application_acronym: `null` is empty",
        '[aws_instance.example (create)] ebs_block_device.1.tags.application_acronym: `"TTO"` is not empty',
        '[aws_instance.example (create)] ebs_block_device.2.tags.application_acronym: `"TTO"` is not empty',
    ]


@mark.passing
def test_wildcard_attribute_keeps_the_unresolved_tail_when_an_item_lacks_the_attribute():
    values_with_paths = handler._wrapper_get_exp_attribute_with_paths(
        "a.*.b.c", {"a": [{"b": {"c": "found"}}, {"no_b": True}]}
    )

    assert values_with_paths == [("a.0.b.c", "found"), ("a.1.b.c", None)]


@mark.passing
def test_wildcard_traversal_without_paths_is_unchanged():
    # `_wrapper_get_exp_attribute` is what the path-tracking traversal replaced, so it has to
    # keep returning the bare values in the same order
    input_data = {"a": [{"b": {"c": ["val1", "val3"]}}, {"b": {"c": ["val8", "val4"]}}, {"d": {}}]}

    assert handler._wrapper_get_exp_attribute("a.*.b.c.*", input_data) == ["val1", "val3", "val8", "val4", None]


@mark.passing
def test_attribute_not_found_names_each_resource_separately():
    # A `*` resource type reports the missing attribute once per resource, and those messages
    # were previously indistinguishable from one another
    result = evaluate("input_costcenter_tags.json", "policy_star_restype_should_skip.json")

    assert messages_of(result) == [
        "[aws_instance.web (create)] attribute: 'shouldnt_exist' is not found",
        "[aws_s3_bucket.logs (create)] attribute: 'shouldnt_exist' is not found",
        "[aws_vpc.main (create)] attribute: 'shouldnt_exist' is not found",
    ]


@mark.passing
def test_count_message_is_labelled_with_the_resource_type():
    # A count belongs to a resource type rather than to any one resource, so it is labelled with
    # the type and has no planned action
    result = evaluate_provider_args(
        {"operation_type": "count", "terraform_resource_type": "aws_vpc"},
        {"type": "GreaterThan", "value": 10},
        "input.json",
    )

    assert messages_of(result) == ["[aws_vpc] count: `2` is not greater than `10`"]
    assert contexts_of(result) == [
        {"operation_type": "count", "resource_type": "aws_vpc", "label": "aws_vpc", "attribute": "count"}
    ]


@mark.passing
def test_action_message_does_not_repeat_the_action():
    # The evaluated value already is the action, so it is not also shown next to the address
    result = evaluate_provider_args(
        {"operation_type": "action", "terraform_resource_type": "aws_vpc"},
        {"type": "ContainedIn", "value": ["create", "update"]},
        "input.json",
    )

    assert messages_of(result) == [
        '[aws_vpc.this[0]] action: Found `"create"` inside `["create", "update"]`',
        '[aws_vpc.this[0]] action: Found `"create"` inside `["create", "update"]`',
    ]


@mark.passing
def test_destroy_approval_names_the_resource_being_destroyed():
    """
    A destroy-approval gate is one `action` evaluator over `*`, so it emits a result per resource
    and every one of them reads `"no-op"` is not equal to `"delete"`. The single line that matters
    used to be buried in a wall of identical lines that named nothing, and finding the resource
    behind it meant counting to the same position in `resource_changes`.
    """
    result = evaluate("input_destroy_approval.json", "policy_destroy_approval.json")

    assert result["final_result"] is False

    failed = [item for item in result["evaluators"][0]["result"] if not item["passed"]]
    assert [item["message"] for item in failed] == [
        '[aws_s3_bucket.legacy_state] action: `"delete"` is equal to `"delete"`'
    ]
    assert failed[0]["context"] == {
        "operation_type": "action",
        "resource_type": "aws_s3_bucket",
        "resource_address": "aws_s3_bucket.legacy_state",
        "attribute": "action",
    }


@mark.passing
def test_every_action_result_names_its_own_resource():
    result = evaluate("input_destroy_approval.json", "policy_destroy_approval.json")
    messages = messages_of(result)

    # Twelve resources, seven of them untouched and four created - so eleven of these twelve lines
    # were byte-identical to another one before the context was added
    assert len(messages) == 12
    assert len(set(messages)) == 12
    assert sum(1 for message in messages if message.endswith('`"no-op"` is not equal to `"delete"`')) == 7


@mark.passing
def test_destroy_approval_passes_when_nothing_is_being_destroyed():
    # The same policy over a plan that destroys nothing: it passes, and the results stay readable
    # instead of being a dozen copies of one line
    input_data = load_terraform_plan_json("input_destroy_approval.json")
    for resource_change in input_data["resource_changes"]:
        if resource_change["change"]["actions"] == ["delete"]:
            resource_change["change"]["actions"] = ["no-op"]

    result = start_policy_evaluation_from_dict(load_policy_from_fixtures("policy_destroy_approval.json"), input_data)

    assert result["final_result"] is True
    assert all(item["passed"] for item in result["evaluators"][0]["result"])
    assert '[aws_s3_bucket.legacy_state] action: `"no-op"` is not equal to `"delete"`' in messages_of(result)


@mark.passing
def test_provider_config_and_terraform_version_messages():
    result = evaluate_provider_args(
        {
            "operation_type": "provider_config",
            "terraform_provider_full_name": "registry.terraform.io/hashicorp/aws",
            "attribute": "region",
        },
        {"type": "Equals", "value": "us-east-1"},
        "input_instance_deps_s3.json",
    )
    assert messages_of(result) == [
        '[provider registry.terraform.io/hashicorp/aws] region: `"eu-central-1"` is not equal to `"us-east-1"`'
    ]

    # There is no resource to name, so the attribute leads the message on its own
    result = evaluate_provider_args(
        {"operation_type": "terraform_version"}, {"type": "Equals", "value": "9.9.9"}, "input_instance_deps_s3.json"
    )
    assert messages_of(result) == ['terraform_version: `"1.4.5"` is not equal to `"9.9.9"`']

    result = evaluate_provider_args(
        {"operation_type": "direct_dependencies", "terraform_resource_type": "aws_instance"},
        {"type": "Contains", "value": "aws_kms_key"},
        "input_instance_deps_s3.json",
    )
    assert messages_of(result) == [
        '[aws_instance.example_c] depends_on: Failed to find `"aws_kms_key"` inside `["aws_s3_bucket"]`'
    ]


@mark.passing
def test_provider_argument_errors_stay_uncontextualised():
    # This error is about the policy rather than about a resource, so there is nothing to name
    result = evaluate_provider_args({"operation_type": "nope"}, {"type": "Equals", "value": 1}, "input.json")

    assert messages_of(result) == ["operation_type: 'nope' is not supported (severity_value: 99)"]
    assert contexts_of(result) == [None]
