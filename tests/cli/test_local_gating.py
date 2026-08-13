"""
The local surface can gate, opt-in, without breaking the callers that rely on it not gating.

`tirith -policy-path … -input-path …` has always exited 0 whether the policy passed or failed. That
made it useless as a CI gate on its own -- the only way to get an exit code that meant something was
to talk to StackGuardian, which is a poor answer for the path most open-source users are on.

`--fail-on-error` fixes it without changing anything by default. The default is asserted here as
carefully as the new behaviour is: flipping it would turn every existing green pipeline red on upgrade,
which is exactly the kind of change that gets a tool pinned forever.

The interesting cases are the ones that are neither a pass nor a violation. `final_result` is
tri-state: True passed, False said no, and **None means nothing ran** -- every check skipped. None is
not a pass, and it is not a violation either, so it exits 1: 3 means the infrastructure violates a
policy, 1 means tirith could not tell you.

The first attempt at this gated on `errors` and inverted both halves. `errors` looks like a
tool-failure signal and is not -- it also carries the informational "these ids are not defined and
have been removed" note, so a genuine violation whose expression contained a typo exited 1 while a
policy naming an unknown provider exited 3. Both directions are tested below.
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


def test_an_unsupported_operator_is_one_not_three(tmp_path):
    """
    `&` is not an operator the evaluator implements. It raises, so this exits 1 through the exception
    handler rather than through the verdict branch -- worth having as an end-to-end assertion, but it
    does not exercise the tri-state logic. The two tests below do.
    """
    broken = dict(POLICY, eval_expression="ev & nonexistent")

    assert main(_write(tmp_path, broken) + ["--fail-on-error"]) == ExitStatus.ERROR


def test_a_policy_that_checked_nothing_is_one_not_three(tmp_path):
    """
    `final_result: None` -- every check skipped, because `error_tolerance` swallowed a provider that
    found nothing. Nothing ran, so there is no verdict: not a pass, and not a violation either.

    This is the case the flag exists for. Reporting 0 would be a green gate over an empty check, and
    reporting 3 would tell someone their infrastructure violates a policy that never looked at it.
    """
    skipped = dict(POLICY)
    skipped["evaluators"] = [
        dict(
            POLICY["evaluators"][0],
            condition={"type": "Equals", "value": "x", "error_tolerance": 2},
            provider_args={
                "operation_type": "attribute",
                "terraform_resource_type": "aws_nonexistent",
                "terraform_resource_attribute": "nope",
            },
        )
    ]

    assert main(_write(tmp_path, skipped) + ["--fail-on-error"]) == ExitStatus.ERROR


def test_a_violation_is_three_even_when_the_expression_names_an_undefined_id(tmp_path):
    """
    A regression test for an inversion this had shipped.

    An `eval_expression` mentioning an id that does not exist produces an *informational* note in
    `errors` -- "the following evaluator ids are not defined and have been removed" -- alongside a
    perfectly real verdict. Gating on `errors` therefore reported a genuine violation as a tool
    failure, which is the more dangerous direction: a broken gate looks like an outage and gets
    retried, or worse, ignored.
    """
    typo = dict(POLICY, eval_expression="ev && nonexistent")

    assert main(_write(tmp_path, typo) + ["--fail-on-error"]) == ExitStatus.ERROR_POLICY_FAILED


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
