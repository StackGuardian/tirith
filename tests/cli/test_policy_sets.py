"""
Running many policies in one invocation: directories and `--pack`.

Two contracts are asserted here, and they pull in opposite directions.

The first is that nothing moved. `-policy-path <file>` is the surface every existing caller uses
and its result document is byte-pinned elsewhere, so a set run has to be a *different* shape
reached by a different request. The rule is that the shape follows how the run was asked for --
a directory or a `--pack` is a set, a file is not -- and not how many policies happened to match,
so a directory holding one policy still reports as a set.

The second is that `skipped` is not a failure. A policy only applies to plans that touch the
resource it names, so across any pack of real size most policies skip. If a skip counted as an
error, every pack run would be red no matter how compliant the infrastructure was, and the exit
code would carry no information at all.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))

from tirith import packs
from tirith.cli import main
from tirith.status import ExitStatus

PLAN = {
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
                "after": {"instance_type": "m5.24xlarge"},
                "after_sensitive": {},
            },
        }
    ],
}


def _policy(policy_id, resource_type, value):
    return {
        "meta": {
            "id": policy_id,
            "name": policy_id,
            "required_provider": "stackguardian/terraform_plan",
            "version": "v1",
        },
        "evaluators": [
            {
                "id": "ev",
                "condition": {"type": "Equals", "value": value, "error_tolerance": 1},
                "provider_args": {
                    "operation_type": "attribute",
                    "terraform_resource_attribute": "instance_type",
                    "terraform_resource_type": resource_type,
                },
            }
        ],
        "eval_expression": "ev",
    }


def _tree(tmp_path, policies):
    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()
    for policy in policies:
        (policy_dir / f"{policy['meta']['id']}.json").write_text(json.dumps(policy))
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(PLAN))
    return ["-policy-path", str(policy_dir), "-input-path", str(plan_path)]


def _run_json(capsys, args):
    main(args + ["--json"])
    return json.loads(capsys.readouterr().out)


def test_a_directory_reports_a_summary(tmp_path, capsys):
    args = _tree(
        tmp_path,
        [
            _policy("passes", "aws_instance", "m5.24xlarge"),
            _policy("fails", "aws_instance", "t3.micro"),
            # No aws_db_instance in the plan, so this one skips rather than failing.
            _policy("skips", "aws_db_instance", "t3.micro"),
        ],
    )
    result = _run_json(capsys, args)
    assert result["summary"] == {"total": 3, "passed": 1, "failed": 1, "skipped": 1, "errored": 0}
    assert result["final_result"] is False
    assert [p["policy"] for p in result["policies"]] == ["fails.json", "passes.json", "skips.json"]


def test_each_policy_keeps_its_own_result_document(tmp_path, capsys):
    args = _tree(tmp_path, [_policy("passes", "aws_instance", "m5.24xlarge")])
    result = _run_json(capsys, args)
    (only,) = result["policies"]
    # Everything a single-policy run returns is still there, plus the name.
    assert set(only) >= {"policy", "meta", "final_result", "evaluators", "errors", "eval_expression"}


def test_a_directory_of_one_is_still_a_set(tmp_path, capsys):
    """The shape follows how the run was asked for, not how many policies matched."""
    args = _tree(tmp_path, [_policy("passes", "aws_instance", "m5.24xlarge")])
    result = _run_json(capsys, args)
    assert "summary" in result


def test_a_single_file_is_not_a_set(tmp_path, capsys):
    _tree(tmp_path, [_policy("passes", "aws_instance", "m5.24xlarge")])
    args = [
        "-policy-path",
        str(tmp_path / "policies" / "passes.json"),
        "-input-path",
        str(tmp_path / "plan.json"),
    ]
    result = _run_json(capsys, args)
    assert "summary" not in result
    assert result["final_result"] is True


def test_skipped_policies_alone_are_one_not_three(tmp_path):
    """
    Nothing reached a verdict, so tirith cannot tell you anything -- 1, not 3 and not 0. The same
    rule the single-policy path applies to `final_result: None`.
    """
    args = _tree(tmp_path, [_policy("skips", "aws_db_instance", "t3.micro")])
    assert main(args + ["--fail-on-error"]) == ExitStatus.ERROR


def test_skipped_policies_do_not_drag_a_passing_run_down(tmp_path):
    args = _tree(
        tmp_path,
        [
            _policy("passes", "aws_instance", "m5.24xlarge"),
            _policy("skips", "aws_db_instance", "t3.micro"),
        ],
    )
    assert main(args + ["--fail-on-error"]) == ExitStatus.SUCCESS


def test_one_failure_among_many_exits_three(tmp_path):
    args = _tree(
        tmp_path,
        [
            _policy("passes", "aws_instance", "m5.24xlarge"),
            _policy("fails", "aws_instance", "t3.micro"),
            _policy("skips", "aws_db_instance", "t3.micro"),
        ],
    )
    assert main(args + ["--fail-on-error"]) == ExitStatus.ERROR_POLICY_FAILED


def test_a_set_still_exits_zero_without_fail_on_error(tmp_path):
    args = _tree(tmp_path, [_policy("fails", "aws_instance", "t3.micro")])
    assert main(args) == ExitStatus.SUCCESS


def test_a_broken_policy_does_not_take_the_run_down(tmp_path, capsys):
    args = _tree(tmp_path, [_policy("passes", "aws_instance", "m5.24xlarge")])
    (tmp_path / "policies" / "broken.json").write_text("{not json")
    result = _run_json(capsys, args)
    assert result["summary"]["errored"] == 1
    assert result["summary"]["passed"] == 1


def test_an_unknown_pack_is_reported_not_raised(tmp_path):
    args = _tree(tmp_path, [])
    assert main(["--pack", "no-such-pack"] + args[2:]) == ExitStatus.ERROR


def test_list_packs_exits_zero(capsys):
    assert main(["--list-packs"]) == ExitStatus.SUCCESS
    assert capsys.readouterr().out


@pytest.mark.skipif(not packs.list_packs(), reason="no packs bundled")
def test_a_bundled_pack_runs(tmp_path, capsys):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(PLAN))
    pack = packs.list_packs()[0]
    result = _run_json(capsys, ["--pack", pack.name, "-input-path", str(plan_path)])
    assert result["summary"]["total"] == len(packs.pack_policy_paths(pack))
    # The point of the summary: on a one-resource plan almost everything skips, and that is fine.
    assert result["summary"]["skipped"] > 0
    assert all(p["policy"].startswith(f"{pack.name}/") for p in result["policies"])
