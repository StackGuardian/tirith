"""
Tests for infracost input with more than one project.

`infracost breakdown` writes one entry in `projects` per Terraform directory it finds. Only the
first one used to be summed, so a cost limit passed whenever the expensive project was not first.
"""

from pytest import mark

from tirith.core.core import start_policy_evaluation_from_dict
from tirith.providers.infracost import handler


INPUT = {
    "currency": "USD",
    "projects": [
        {
            "name": "networking",
            "breakdown": {"resources": [{"name": "aws_nat_gateway.main", "monthlyCost": "10"}]},
        },
        {
            "name": "data",
            "breakdown": {"resources": [{"name": "aws_redshift_cluster.warehouse", "monthlyCost": "5000"}]},
        },
    ],
}


def evaluate(provider_args, condition):
    policy = {
        "meta": {"version": "v1", "required_provider": "stackguardian/infracost"},
        "evaluators": [{"id": "cost", "provider_args": provider_args, "condition": condition}],
        "eval_expression": "cost",
    }
    return start_policy_evaluation_from_dict(policy, INPUT)


@mark.passing
def test_total_cost_sums_every_project():
    result = handler.provide({"operation_type": "total_monthly_cost", "resource_type": ["*"]}, INPUT)

    assert result[0]["value"] == 5010
    assert result[0]["context"]["matched_resources"] == 2


@mark.passing
def test_resource_type_is_found_outside_the_first_project():
    result = handler.provide({"operation_type": "total_monthly_cost", "resource_type": ["aws_redshift_cluster"]}, INPUT)

    assert result[0]["value"] == 5000
    assert result[0]["context"]["matched_resources"] == 1


@mark.passing
def test_cost_limit_fails_when_a_later_project_exceeds_it():
    result = evaluate(
        {"operation_type": "total_monthly_cost", "resource_type": ["*"]},
        {"type": "LessThanEqualTo", "value": 1000},
    )

    assert result["final_result"] is False
