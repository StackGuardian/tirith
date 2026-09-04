"""
Tests for the context the infracost provider attaches to its results.

A cost message used to be the comparison and nothing else -- ```0` is less than `20``` -- which
says neither which cost was measured nor what it covered. Monthly and hourly figures are
indistinguishable, and a `resource_type` matching nothing produces a real-looking 0 that quietly
satisfies a `LessThan`.
"""

import json
import os

from pytest import mark

from tirith.core.core import start_policy_evaluation_from_dict
from tirith.providers.infracost import handler


def load_json(name):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), name)) as f:
        return json.load(f)


INPUT = load_json("input.json")


def evaluate(provider_args, condition, input_data=None):
    policy = {
        "meta": {"version": "v1", "required_provider": "stackguardian/infracost"},
        "evaluators": [{"id": "cost", "provider_args": provider_args, "condition": condition}],
        "eval_expression": "cost",
    }
    return start_policy_evaluation_from_dict(policy, input_data if input_data is not None else INPUT)


def results_of(result):
    return result["evaluators"][0]["result"]


@mark.passing
def test_total_cost_message_names_the_metric_and_its_scope():
    result = evaluate(
        {"operation_type": "total_monthly_cost", "resource_type": ["*"]},
        {"type": "LessThanEqualTo", "value": 20},
    )

    assert [item["message"] for item in results_of(result)] == [
        "[all resources (2 resources)] total_monthly_cost: `300.1` is not less than or equal to `20`"
    ]


@mark.passing
def test_specific_resource_types_are_named():
    result = evaluate(
        {"operation_type": "total_monthly_cost", "resource_type": ["aws_eks_cluster", "aws_s3_bucket"]},
        {"type": "LessThanEqualTo", "value": -1},
    )

    assert [item["message"] for item in results_of(result)] == [
        "[aws_eks_cluster, aws_s3_bucket (1 resource)] total_monthly_cost: `100.1` is not less than or equal to `-1`"
    ]


@mark.passing
def test_hourly_and_monthly_are_no_longer_indistinguishable():
    monthly = evaluate(
        {"operation_type": "total_monthly_cost", "resource_type": ["*"]}, {"type": "LessThan", "value": 1}
    )
    hourly = evaluate({"operation_type": "total_hourly_cost", "resource_type": ["*"]}, {"type": "LessThan", "value": 1})

    assert "total_monthly_cost:" in results_of(monthly)[0]["message"]
    assert "total_hourly_cost:" in results_of(hourly)[0]["message"]


@mark.passing
def test_a_resource_type_matching_nothing_says_so_instead_of_reporting_a_bare_zero():
    # The trap this closes: a typo'd resource_type costs 0, and `LessThan 20` passes while
    # measuring nothing at all. The verdict is unchanged -- the message now admits why.
    result = evaluate(
        {"operation_type": "total_monthly_cost", "resource_type": ["aws_instances"]},
        {"type": "LessThan", "value": 20},
    )
    item = results_of(result)[0]

    assert item["passed"] is True
    assert item["message"] == "[aws_instances (0 resources)] total_monthly_cost: `0` is less than `20`"
    assert item["context"]["matched_resources"] == 0


@mark.passing
def test_context_carries_the_same_detail_as_the_message():
    result = evaluate(
        {"operation_type": "total_monthly_cost", "resource_type": ["aws_s3_bucket"]},
        {"type": "LessThan", "value": 20},
    )

    assert results_of(result)[0]["context"] == {
        "operation_type": "total_monthly_cost",
        "label": "aws_s3_bucket",
        "attribute": "total_monthly_cost",
        "resource_type": ["aws_s3_bucket"],
        "matched_resources": 1,
        "qualifier": "1 resource",
        "currency": "USD",
    }


@mark.passing
def test_a_string_resource_type_is_accepted_as_well_as_a_list():
    result = evaluate(
        {"operation_type": "total_monthly_cost", "resource_type": "aws_s3_bucket"},
        {"type": "LessThan", "value": 20},
    )

    assert "[aws_s3_bucket (1 resource)]" in results_of(result)[0]["message"]


@mark.passing
def test_a_malformed_breakdown_names_the_metric_it_could_not_measure():
    # Previously "projects not found in input_data" arrived with no indication of which
    # evaluator it belonged to
    result = evaluate(
        {"operation_type": "total_monthly_cost", "resource_type": ["*"]},
        {"type": "LessThan", "value": 20},
        input_data={"currency": "USD"},
    )
    item = results_of(result)[0]

    assert item["passed"] is False
    assert item["message"] == "[all resources] total_monthly_cost: 'projects not found in input_data'"


@mark.passing
def test_missing_provider_args_still_report_without_a_context():
    # Nothing is known about what was being measured, so there is nothing to name
    result = evaluate({"resource_type": ["*"]}, {"type": "LessThan", "value": 20})
    item = results_of(result)[0]

    assert item["passed"] is False
    assert item["message"] == "'resource_type/operation_type not found in provider_args'"
    assert "context" not in item


@mark.passing
def test_the_cost_walks_still_return_the_same_totals():
    # The walks now return (total, matched_count); the totals themselves must not move
    get_all_costs = getattr(handler, "__get_all_costs")
    get_resources_costs = getattr(handler, "__get_resources_costs")

    assert get_all_costs("total_monthly_cost", INPUT) == (300.1, 2)
    assert get_resources_costs(["aws_s3_bucket"], "total_monthly_cost", INPUT) == (100.1, 1)
