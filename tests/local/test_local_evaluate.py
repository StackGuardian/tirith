"""
Unit coverage for policy discovery, input preparation and the engine subprocess.

The pinned-argv test near the bottom is the load-bearing one: it is what keeps the frozen `--json`
contract as the interface between this package and the engine, now that both live in the same
distribution and calling the engine's Python API directly has become easy.
"""

import json
import sys

import pytest
from conftest import POLICY, plan

from tirith.local import evaluate
from tirith.local.evaluate import LocalError
from tirith.platform import report


def test_a_named_file_is_taken_as_given(tmp_path):
    """
    Naming a file explicitly is an instruction. Reporting "that is not a policy" is more useful than
    silently evaluating nothing.
    """
    path = tmp_path / "not-really.json"
    path.write_text("{}")

    assert evaluate.discover_policies(str(path)) == [str(path)]


def test_a_directory_prefers_the_tirith_suffix(tmp_path):
    (tmp_path / "a.tirith.json").write_text(json.dumps(POLICY))
    (tmp_path / "b.json").write_text(json.dumps(POLICY))

    found = evaluate.discover_policies(str(tmp_path))

    assert [p.rsplit("/", 1)[-1] for p in found] == ["a.tirith.json"]


def test_a_directory_without_the_suffix_falls_back_to_shape(tmp_path):
    (tmp_path / "policy.json").write_text(json.dumps(POLICY))

    found = evaluate.discover_policies(str(tmp_path))

    assert [p.rsplit("/", 1)[-1] for p in found] == ["policy.json"]


def test_the_input_document_sitting_in_the_policy_directory_is_not_evaluated_as_a_policy(tmp_path):
    """
    Load-bearing rather than defensive. A policy directory routinely also holds the document under
    evaluation; without the shape filter the plan is evaluated *as a policy*, which reports a
    spurious failure and buries the real findings.
    """
    (tmp_path / "policy.json").write_text(json.dumps(POLICY))
    (tmp_path / "plan.json").write_text(json.dumps(plan()))

    found = evaluate.discover_policies(str(tmp_path))

    assert [p.rsplit("/", 1)[-1] for p in found] == ["policy.json"]


def test_a_glob_is_filtered_by_shape_too(tmp_path):
    (tmp_path / "policy.json").write_text(json.dumps(POLICY))
    (tmp_path / "plan.json").write_text(json.dumps(plan()))

    found = evaluate.discover_policies(str(tmp_path / "*.json"))

    assert [p.rsplit("/", 1)[-1] for p in found] == ["policy.json"]


def test_an_empty_policy_path_finds_nothing(tmp_path):
    assert evaluate.discover_policies("") == []
    assert evaluate.discover_policies(str(tmp_path / "nowhere")) == []


def test_a_terraform_state_check_evaluates_the_state_not_a_discovered_plan(tmp_path):
    """
    `--state-path` is how the platform path names the document for a terraform_state check. Ignoring
    it sent local mode to discovery, which finds plan.json -- so the two modes evaluated *different
    documents* from identical inputs, and a violation present only in the state was reported as a
    pass.
    """
    (tmp_path / "plan.json").write_text(json.dumps(plan()))
    state = tmp_path / "state.json"
    state.write_text(
        json.dumps({"values": {"root_module": {"resources": [{"address": "aws_instance.only-in-state"}]}}})
    )

    resolved, _ = evaluate.prepare_input(
        None, None, None, "terraform_state", str(tmp_path), str(tmp_path), state_path=str(state)
    )

    with open(resolved) as f:
        assert "only-in-state" in json.dumps(json.load(f))


def test_a_json_document_is_passed_through_unmasked(tmp_path):
    """
    `json` and `kubernetes` carry no sensitivity markers to mask by, and tirith reads YAML for them,
    which a JSON round-trip here would break. So the original path is returned, not a copy.
    """
    document = tmp_path / "anything.json"
    document.write_text(json.dumps({"hello": "world"}))

    resolved, redactions = evaluate.prepare_input(str(document), None, None, "json", str(tmp_path), str(tmp_path))

    assert resolved == str(document)
    assert redactions == 0


def test_a_json_document_must_be_named(tmp_path):
    with pytest.raises(LocalError, match="--input-path is required"):
        evaluate.prepare_input(None, None, None, "json", str(tmp_path), str(tmp_path))


def test_input_path_and_plan_file_cannot_be_combined(tmp_path):
    with pytest.raises(LocalError, match="cannot be combined"):
        evaluate.prepare_input("a.json", "tfplan", None, "terraform_plan", str(tmp_path), str(tmp_path))


def test_a_missing_document_raises_rather_than_evaluating_nothing(tmp_path):
    with pytest.raises(LocalError, match="not found"):
        evaluate.prepare_input(str(tmp_path / "gone.json"), None, None, "terraform_plan", str(tmp_path), str(tmp_path))


def test_a_sensitive_value_is_masked_and_counted(tmp_path):
    document = tmp_path / "plan.json"
    document.write_text(json.dumps(plan(secret="hunter2")))

    resolved, redactions = evaluate.prepare_input(
        str(document), None, None, "terraform_plan", str(tmp_path), str(tmp_path)
    )

    assert redactions >= 1
    with open(resolved) as f:
        assert "hunter2" not in f.read()


def test_the_engine_is_invoked_as_a_subprocess_against_the_frozen_json_contract():
    """
    Pinned deliberately. That stdout document is the most stable interface tirith has -- it is
    byte-for-byte pinned by tests/core/test_output_compatibility.py -- whereas the engine's Python
    API carries no such promise. Now that this code lives inside the package, calling
    `start_policy_evaluation` directly would save an interpreter start per policy and silently couple
    local mode to internals. This makes that a deliberate change with a red test, not a tidy-up.

    `sys.executable -m tirith` rather than a `tirith` on PATH: the interpreter that evaluates must be
    the one whose renderer was imported, and a `tirith` on PATH could be a different installation.
    """
    assert evaluate.engine_argv("p.json", "i.json") == [
        sys.executable,
        "-m",
        "tirith",
        "-policy-path",
        "p.json",
        "-input-path",
        "i.json",
    ]


def test_an_unevaluable_policy_becomes_a_visible_fail_carrying_its_reason(tmp_path):
    """
    Not a skip and not a silent drop: the renderer surfaces `exec_err` as `engine: <reason>`, so it
    appears in the report, is distinguishable from a real violation, and is never mistakable for a
    pass.
    """
    broken = tmp_path / "broken.tirith.json"
    broken.write_text(json.dumps({"meta": {}, "evaluators": [{"nonsense": True}]}))
    document = tmp_path / "plan.json"
    document.write_text(json.dumps(plan()))

    policy_results, errored = evaluate.evaluate([str(broken)], str(document))

    assert len(errored) == 1
    rule = policy_results["broken"][0]
    assert rule["result"] == report.FAIL
    assert "exec_err" in rule["evaluations"]["fails"][0]


def test_the_enforcement_matrix(tmp_path):
    """Every recognised spelling, plus the unrecognised case, in one place."""
    document = tmp_path / "plan.json"
    document.write_text(json.dumps(plan()))

    for value, expected, expect_notice in (
        ("soft_mandatory", report.WARN, False),
        ("advisory", report.WARN, False),
        ("approval_required", report.WARN, False),
        ("hard_mandatory", report.FAIL, False),
        ("blocking", report.FAIL, False),
        (None, report.FAIL, False),
        ("who-knows", report.FAIL, True),
    ):
        policy = json.loads(json.dumps(POLICY))
        if value is not None:
            policy["meta"]["enforcement"] = value
        path = tmp_path / "p.tirith.json"
        path.write_text(json.dumps(policy))

        notices = []
        policy_results, _ = evaluate.evaluate([str(path)], str(document), on_unknown_enforcement=notices.append)

        assert policy_results["instance-type"][0]["result"] == expected, value
        assert bool(notices) is expect_notice, value
