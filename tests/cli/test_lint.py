"""
`tirith lint`: the validator behind the interface, run from the command line with Tirith's exit codes.

Exit 3 for a policy with errors is deliberate and mirrors evaluation: the linter saying no about a
policy is a verdict. Exit 1 is reserved for the tool being unable to do its job -- a path that does
not exist, nothing to lint.
"""

import json
import os

import pytest

from tirith import cli
from tirith.status import ExitStatus

GOOD = {
    "meta": {"version": "v1", "required_provider": "stackguardian/terraform_plan", "name": "tags"},
    "evaluators": [
        {
            "id": "tags_present",
            "provider_args": {
                "operation_type": "attribute",
                "terraform_resource_type": "*",
                "terraform_resource_attribute": "tags",
            },
            "condition": {"type": "IsNotEmpty"},
        }
    ],
    "eval_expression": "tags_present",
}


def _write(directory, name, document):
    path = os.path.join(str(directory), name)
    with open(path, "w") as f:
        if isinstance(document, str):
            f.write(document)
        else:
            json.dump(document, f)
    return path


def _bad(**changes):
    policy = json.loads(json.dumps(GOOD))
    policy["evaluators"][0]["condition"].update(changes)
    return policy


def test_a_clean_policy_exits_0_with_a_summary(tmp_path, capsys):
    path = _write(tmp_path, "p.json", GOOD)

    status = cli.main(["lint", path])

    assert status == ExitStatus.SUCCESS
    out = capsys.readouterr().out
    assert out.strip() == "1 policy, 0 errors, 0 warnings"


def test_an_invented_condition_type_is_an_error_and_exits_3(tmp_path, capsys):
    path = _write(tmp_path, "p.json", _bad(type="Exists"))

    status = cli.main(["lint", path])

    assert status == ExitStatus.ERROR_POLICY_FAILED
    out = capsys.readouterr().out
    assert f"{path}:evaluators[0].condition.type: error: 'Exists' is not an evaluator" in out
    assert "1 policy, 1 errors, 0 warnings" in out


def test_error_tolerance_outside_condition_is_an_error(tmp_path, capsys):
    """The trap the skill pack warns about most: the engine ignores it silently, so lint must not."""
    policy = json.loads(json.dumps(GOOD))
    policy["evaluators"][0]["error_tolerance"] = 2
    path = _write(tmp_path, "p.json", policy)

    status = cli.main(["lint", path])

    assert status == ExitStatus.ERROR_POLICY_FAILED
    assert "evaluators[0].error_tolerance: error: Belongs inside `condition`" in capsys.readouterr().out


def test_a_key_another_provider_reads_is_a_warning_and_exits_0(tmp_path, capsys):
    """Warnings do not fail the run by default: the provider ignores the key, the policy still runs."""
    policy = json.loads(json.dumps(GOOD))
    policy["evaluators"][0]["provider_args"]["attribute_path"] = "spec.x"
    path = _write(tmp_path, "p.json", policy)

    status = cli.main(["lint", path])

    assert status == ExitStatus.SUCCESS
    out = capsys.readouterr().out
    assert "provider_args.attribute_path: warning: Not read by operation 'attribute'" in out
    assert "0 errors, 1 warnings" in out


def test_strict_promotes_warnings_to_the_exit_code(tmp_path):
    policy = json.loads(json.dumps(GOOD))
    policy["evaluators"][0]["provider_args"]["attribute_path"] = "spec.x"
    path = _write(tmp_path, "p.json", policy)

    assert cli.main(["lint", "--strict", path]) == ExitStatus.ERROR_POLICY_FAILED


def test_an_evaluator_the_expression_never_names_is_reported(tmp_path, capsys):
    policy = json.loads(json.dumps(GOOD))
    policy["evaluators"].append(dict(policy["evaluators"][0], id="orphan"))
    path = _write(tmp_path, "p.json", policy)

    cli.main(["lint", path])

    assert "eval_expression: warning: Check 'orphan' runs but is not used in the expression" in capsys.readouterr().out


def test_invalid_json_is_an_error_on_the_file(tmp_path, capsys):
    path = _write(tmp_path, "p.json", '{"meta": ')

    status = cli.main(["lint", path])

    assert status == ExitStatus.ERROR_POLICY_FAILED
    assert f"{path}:<file>: error: not valid JSON" in capsys.readouterr().out


def test_a_missing_path_exits_1(tmp_path, capsys):
    status = cli.main(["lint", os.path.join(str(tmp_path), "nope")])

    assert status == ExitStatus.ERROR
    assert "no such file or directory" in capsys.readouterr().err


def test_a_directory_with_no_policies_exits_1(tmp_path, capsys):
    _write(tmp_path, "plan.json", {"resource_changes": []})

    status = cli.main(["lint", str(tmp_path)])

    assert status == ExitStatus.ERROR
    assert "No policies found" in capsys.readouterr().err


def test_a_directory_walk_reports_ignored_documents_in_the_summary_only(tmp_path, capsys):
    _write(tmp_path, "policy.json", GOOD)
    _write(tmp_path, "input.json", {"resource_changes": []})

    status = cli.main(["lint", str(tmp_path)])

    assert status == ExitStatus.SUCCESS
    captured = capsys.readouterr()
    assert "1 policy, 0 errors, 0 warnings (1 JSON files that are not policies ignored)" in captured.out
    assert "input.json" not in captured.err


def test_an_explicitly_named_non_policy_is_named_on_stderr(tmp_path, capsys):
    good = _write(tmp_path, "policy.json", GOOD)
    plan = _write(tmp_path, "plan.json", {"resource_changes": []})

    status = cli.main(["lint", good, plan])

    assert status == ExitStatus.SUCCESS
    assert f"{plan}: skipped, not a Tirith policy" in capsys.readouterr().err


def test_quiet_prints_findings_only(tmp_path, capsys):
    path = _write(tmp_path, "p.json", _bad(type="Exists"))

    cli.main(["lint", "--quiet", path])

    out = capsys.readouterr().out
    assert "error:" in out
    assert "policies" not in out and "policy," not in out


def test_json_output_is_a_document_with_findings_and_summary(tmp_path, capsys):
    path = _write(tmp_path, "p.json", _bad(type="Exists"))

    status = cli.main(["lint", "--json", path])

    assert status == ExitStatus.ERROR_POLICY_FAILED
    report = json.loads(capsys.readouterr().out)
    assert report["summary"] == {"policies": 1, "errors": 1, "warnings": 0, "ignored": 0}
    assert report["exit_status"] == 3
    (entry,) = report["files"]
    assert entry["path"] == path
    assert entry["findings"][0]["severity"] == "error"
    assert entry["findings"][0]["where"] == "evaluators[0].condition.type"


def test_help_names_the_exit_codes(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["lint", "--help"])

    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    assert "tirith lint" in out
    assert "3 a policy has errors" in out


def test_the_repository_examples_lint_clean():
    """The worked examples shipped with the interface are the reference policies; they must be clean."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    examples = os.path.join(root, "src", "tirith", "tui", "examples")

    assert cli.main(["lint", "--strict", "--quiet", examples]) == ExitStatus.SUCCESS
