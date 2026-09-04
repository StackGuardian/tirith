"""`tirith fmt`: one canonical layout, never a change of meaning."""

import json
import os

import pytest

from tirith import cli
from tirith.fmt import canonical, format_policy
from tirith.status import ExitStatus

SCRAMBLED = {
    "eval_expression": "a && b",
    "evaluators": [
        {
            "condition": {"error_tolerance": 1, "value": ["x", "y"], "type": "ContainedIn"},
            "provider_args": {
                "terraform_resource_type": "aws_s3_bucket",
                "operation_type": "attribute",
                "terraform_resource_attribute": "acl",
            },
            "description": "acl",
            "id": "a",
        },
        {
            "id": "b",
            "provider_args": {"operation_type": "count", "terraform_resource_type": "*"},
            "condition": {"type": "LessThan", "value": 50},
        },
    ],
    "meta": {"name": "n", "required_provider": "stackguardian/terraform_plan", "version": "v1", "custom": True},
}

CANONICAL_TEXT = """{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/terraform_plan",
    "name": "n",
    "custom": true
  },
  "evaluators": [
    {
      "id": "a",
      "description": "acl",
      "provider_args": {
        "operation_type": "attribute",
        "terraform_resource_type": "aws_s3_bucket",
        "terraform_resource_attribute": "acl"
      },
      "condition": {
        "type": "ContainedIn",
        "value": ["x", "y"],
        "error_tolerance": 1
      }
    },
    {
      "id": "b",
      "provider_args": {
        "operation_type": "count",
        "terraform_resource_type": "*"
      },
      "condition": {
        "type": "LessThan",
        "value": 50
      }
    }
  ],
  "eval_expression": "a && b"
}
"""


def _write(directory, name, text):
    path = os.path.join(str(directory), name)
    with open(path, "w") as f:
        f.write(text)
    return path


def _read(path):
    with open(path) as f:
        return f.read()


def test_canonical_orders_keys_and_keeps_unknown_ones_after_known():
    out = canonical(SCRAMBLED)

    assert list(out) == ["meta", "evaluators", "eval_expression"]
    assert list(out["meta"]) == ["version", "required_provider", "name", "custom"]
    assert list(out["evaluators"][0]) == ["id", "description", "provider_args", "condition"]
    assert list(out["evaluators"][0]["provider_args"])[0] == "operation_type"
    assert list(out["evaluators"][0]["condition"]) == ["type", "value", "error_tolerance"]


def test_format_is_the_documented_layout():
    assert format_policy(SCRAMBLED) == CANONICAL_TEXT


def test_format_never_changes_meaning():
    assert json.loads(format_policy(SCRAMBLED)) == SCRAMBLED


def test_format_is_idempotent():
    once = format_policy(SCRAMBLED)
    assert format_policy(json.loads(once)) == once


def test_short_scalar_lists_stay_inline_and_long_ones_expand():
    short = format_policy({"meta": {"tags": ["a", "b"]}})
    assert '"tags": ["a", "b"]' in short

    long_list = ["a-very-long-tag-value-number-%d" % i for i in range(6)]
    expanded = format_policy({"meta": {"tags": long_list}})
    assert '"tags": [\n' in expanded
    assert json.loads(expanded)["meta"]["tags"] == long_list


def test_lists_of_objects_and_empty_containers():
    text = format_policy({"evaluators": [], "meta": {}})
    assert text == '{\n  "meta": {},\n  "evaluators": []\n}\n'


def test_non_ascii_is_kept_as_written():
    assert '"name": "Kosten­stelle"' in format_policy({"meta": {"name": "Kosten­stelle"}})


def test_fmt_rewrites_in_place_and_names_the_file(tmp_path, capsys):
    path = _write(tmp_path, "p.json", json.dumps(SCRAMBLED))

    status = cli.main(["fmt", path])

    assert status == ExitStatus.SUCCESS
    assert capsys.readouterr().out.strip() == path
    assert _read(path) == CANONICAL_TEXT


def test_fmt_leaves_a_canonical_file_alone(tmp_path, capsys):
    path = _write(tmp_path, "p.json", CANONICAL_TEXT)
    before = os.stat(path).st_mtime_ns

    status = cli.main(["fmt", path])

    assert status == ExitStatus.SUCCESS
    assert capsys.readouterr().out == ""
    assert os.stat(path).st_mtime_ns == before


def test_check_exits_3_and_writes_nothing_when_a_file_would_change(tmp_path, capsys):
    original = json.dumps(SCRAMBLED)
    path = _write(tmp_path, "p.json", original)

    status = cli.main(["fmt", "--check", path])

    assert status == ExitStatus.ERROR_POLICY_FAILED
    assert capsys.readouterr().out.strip() == path
    assert _read(path) == original


def test_check_exits_0_when_everything_is_canonical(tmp_path):
    path = _write(tmp_path, "p.json", CANONICAL_TEXT)

    assert cli.main(["fmt", "--check", path]) == ExitStatus.SUCCESS


def test_diff_shows_the_change_and_implies_check(tmp_path, capsys):
    original = json.dumps(SCRAMBLED)
    path = _write(tmp_path, "p.json", original)

    status = cli.main(["fmt", "--diff", path])

    assert status == ExitStatus.ERROR_POLICY_FAILED
    out = capsys.readouterr().out
    assert out.startswith(f"--- {path}\n+++ {path}\n")
    assert '+  "meta": {' in out
    assert _read(path) == original


def test_invalid_json_exits_1_and_is_not_touched(tmp_path, capsys):
    path = _write(tmp_path, "p.json", '{"meta": ')

    status = cli.main(["fmt", path])

    assert status == ExitStatus.ERROR
    assert "not valid JSON" in capsys.readouterr().err
    assert _read(path) == '{"meta": '


def test_a_missing_path_exits_1(tmp_path):
    assert cli.main(["fmt", os.path.join(str(tmp_path), "nope")]) == ExitStatus.ERROR


def test_non_policies_are_never_rewritten(tmp_path, capsys):
    plan = _write(tmp_path, "plan.json", '{"resource_changes":[]}')
    policy = _write(tmp_path, "policy.json", json.dumps(SCRAMBLED))

    status = cli.main(["fmt", str(tmp_path)])

    assert status == ExitStatus.SUCCESS
    assert _read(plan) == '{"resource_changes":[]}'
    assert _read(policy) == CANONICAL_TEXT


def test_help_is_the_fmt_help(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["fmt", "--help"])

    assert excinfo.value.code == 0
    assert "tirith fmt" in capsys.readouterr().out


def test_the_repository_examples_are_canonical():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    examples = os.path.join(root, "src", "tirith", "tui", "examples")

    assert cli.main(["fmt", "--check", examples]) == ExitStatus.SUCCESS
