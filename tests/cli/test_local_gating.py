"""
The local surface can gate, opt-in, without breaking the callers that rely on it not gating.

`tirith -policy-path … -input-path …` has always exited 0 whether the policy passed or failed. That
made it useless as a CI gate on its own -- the only way to get an exit code that meant something was
to talk to StackGuardian, which is a poor answer for the path most open-source users are on.

`--fail-on-error` fixes it without changing anything by default. The default is asserted here as
carefully as the new behaviour is: flipping it would turn every existing green pipeline red on upgrade,
which is exactly the kind of change that gets a tool pinned forever.

The interesting case is the third one. `final_result` is False both for a policy that genuinely failed
and for one that could not be evaluated, and those must not share an exit code -- 3 means the
infrastructure violates a policy, 1 means tirith could not tell you. A CI job that treats them alike
reports an outage as a violation.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))

from tirith.cli import main
from tirith.status import ExitStatus

POLICY = {
    "meta": {
        "id": "instance-type",
        "name": "instance types are approved",
        "required_provider": "stackguardian/terraform_plan",
        "version": "v1",
    },
    "evaluators": [
        {
            "id": "ev",
            "description": "instance_type must be t3.micro",
            "condition": {"type": "Equals", "value": "t3.micro", "error_tolerance": 0},
            "provider_args": {
                "operation_type": "attribute",
                "terraform_resource_attribute": "instance_type",
                "terraform_resource_type": "aws_instance",
            },
        }
    ],
    "eval_expression": "ev",
}


def _plan(instance_type):
    return {
        "format_version": "1.2",
        "terraform_version": "1.5.7",
        "resource_changes": [
            {
                "address": "aws_instance.app",
                "mode": "managed",
                "type": "aws_instance",
                "name": "app",
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": {"instance_type": instance_type},
                    "after_sensitive": {},
                },
            }
        ],
    }


def _write(tmp_path, policy, instance_type="m5.24xlarge"):
    policy_path = tmp_path / "policy.json"
    plan_path = tmp_path / "plan.json"
    policy_path.write_text(json.dumps(policy))
    plan_path.write_text(json.dumps(_plan(instance_type)))
    return ["-policy-path", str(policy_path), "-input-path", str(plan_path), "--json"]


def test_a_failing_policy_still_exits_zero_by_default(tmp_path):
    """
    The compatibility guarantee. Anyone already running this in CI is relying on it, knowingly or not,
    and a silent change would break their pipeline on an upgrade they did not ask for.
    """
    assert main(_write(tmp_path, POLICY)) == ExitStatus.SUCCESS


def test_a_failing_policy_exits_three_with_fail_on_error(tmp_path):
    assert main(_write(tmp_path, POLICY) + ["--fail-on-error"]) == ExitStatus.ERROR_POLICY_FAILED


def test_a_passing_policy_exits_zero_with_fail_on_error(tmp_path):
    args = _write(tmp_path, POLICY, instance_type="t3.micro")
    assert main(args + ["--fail-on-error"]) == ExitStatus.SUCCESS


def test_a_policy_that_could_not_be_evaluated_is_one_not_three(tmp_path):
    """
    The distinction the exit codes exist to draw.

    `&` is not an operator the evaluator implements, so the expression cannot be evaluated at all --
    and the result carries `final_result: False` exactly as a real violation would. Reporting 3 here
    would tell a caller their infrastructure violates a policy when in fact nothing was checked.
    """
    broken = dict(POLICY, eval_expression="ev & nonexistent")

    assert main(_write(tmp_path, broken) + ["--fail-on-error"]) == ExitStatus.ERROR


def test_a_missing_variable_is_one_not_three(tmp_path):
    """
    The other unevaluable shape, and it fails differently: this path returns errors and no
    `final_result` key at all, so a check that only looked at `final_result` would read the absence as
    falsy and report a violation.
    """
    parameterised = dict(POLICY, eval_expression="ev")
    parameterised["evaluators"] = [
        dict(POLICY["evaluators"][0], condition={"type": "Equals", "value": "{{ var.expected }}", "error_tolerance": 0})
    ]

    exit_status = main(_write(tmp_path, parameterised) + ["--fail-on-error"])

    assert exit_status != ExitStatus.ERROR_POLICY_FAILED, "an unresolved variable is not a policy violation"


@pytest.mark.parametrize("status", [ExitStatus.SUCCESS, ExitStatus.ERROR, ExitStatus.ERROR_POLICY_FAILED])
def test_the_codes_this_relies_on_are_distinct(status):
    """Guards the premise: 0, 1 and 3 have to be three different numbers for any of this to mean anything."""
    others = {ExitStatus.SUCCESS, ExitStatus.ERROR, ExitStatus.ERROR_POLICY_FAILED} - {status}
    assert status.value not in {other.value for other in others}
