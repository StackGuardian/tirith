"""
Tests for the MCP tools.

They import tirith.mcp.tools directly, never tirith.mcp.server, so the whole file runs on Python
3.8 where the MCP SDK cannot be installed. That split is the reason tools.py holds the behaviour
and server.py only describes it.
"""

import json
import os
import re

import pytest

from tirith.core.evaluators import EVALUATORS_DICT
from tirith.mcp import tools

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
EXAMPLES = os.path.join(REPO, "src", "tirith", "tui", "examples")


def _example(name):
    with open(os.path.join(EXAMPLES, name, "policy.json")) as handle:
        policy = json.load(handle)
    with open(os.path.join(EXAMPLES, name, "input.json")) as handle:
        document = json.load(handle)
    return policy, document


# --------------------------------------------------------------------- evaluate ---


def test_evaluate_reports_a_real_failure():
    policy, document = _example("01-required-tags")
    out = tools.evaluate(policy, document)
    assert out["verdict"]["outcome"] == "failed"
    assert out["verdict"]["exit_code"] == 3
    assert out["result"]["final_result"] is False


def test_evaluate_reports_a_real_pass():
    policy, document = _example("03-cost-ceiling")
    out = tools.evaluate(policy, document)
    assert out["verdict"]["outcome"] == "passed"
    assert out["verdict"]["exit_code"] == 0


def test_unevaluated_is_not_reported_as_a_pass():
    """
    The distinction the whole exit-code contract exists to protect. A policy whose checks were
    all skipped must never come back as `passed`, and must not come back as exit 3 either -- it
    is not a violation, it is an absence of an answer.
    """
    verdict = tools._exit_code_for({"final_result": None})
    assert verdict["outcome"] == "unevaluated"
    assert verdict["exit_code"] == 1
    assert "NOT a pass" in verdict["meaning"]


def test_missing_final_result_is_an_error_not_a_verdict():
    verdict = tools._exit_code_for({})
    assert verdict["outcome"] == "errored"
    assert verdict["exit_code"] == 1


# ------------------------------------------------------------------ lint_policy ---


@pytest.mark.parametrize("name", sorted(os.listdir(EXAMPLES)))
def test_shipped_examples_lint_clean(name):
    """Every policy we ship should pass our own linter, or one of the two is wrong."""
    policy, _ = _example(name)
    report = tools.lint_policy(policy)
    assert report["ok"], report["problems"]


def test_lint_rejects_an_invented_condition_type():
    """
    The highest-value lint. An unknown condition type reaches the engine as an ordinary failed
    check with no error attached, so it reads as a real infrastructure violation.
    """
    report = tools.lint_policy(
        {
            "meta": {"version": "v1", "required_provider": "stackguardian/terraform_plan", "name": "n"},
            "evaluators": [
                {"id": "a", "provider_args": {"operation_type": "attribute"}, "condition": {"type": "Exists"}}
            ],
            "eval_expression": "a",
        }
    )
    assert not report["ok"]
    assert any("Exists" in p["message"] for p in report["problems"])


def test_lint_flags_an_evaluator_the_expression_never_references():
    report = tools.lint_policy(
        {
            "meta": {"version": "v1", "required_provider": "stackguardian/terraform_plan", "name": "n"},
            "evaluators": [
                {"id": "a", "provider_args": {"operation_type": "attribute"}, "condition": {"type": "IsNotEmpty"}},
                {"id": "orphan", "provider_args": {"operation_type": "attribute"}, "condition": {"type": "IsEmpty"}},
            ],
            "eval_expression": "a",
        }
    )
    assert report["ok"], "an unreferenced evaluator is a warning, not an error"
    assert any("orphan" in p["message"] for p in report["problems"])


def test_lint_rejects_duplicate_evaluator_ids():
    report = tools.lint_policy(
        {
            "meta": {"version": "v1", "required_provider": "stackguardian/terraform_plan", "name": "n"},
            "evaluators": [
                {"id": "a", "provider_args": {"operation_type": "attribute"}, "condition": {"type": "IsEmpty"}},
                {"id": "a", "provider_args": {"operation_type": "attribute"}, "condition": {"type": "IsEmpty"}},
            ],
            "eval_expression": "a",
        }
    )
    assert not report["ok"]


def test_lint_survives_rubbish():
    assert tools.lint_policy("not a policy")["ok"] is False


# ------------------------------------------------------------ describe_provider ---


def test_describe_provider_lists_every_real_condition_type():
    """Sourced from the engine's registry, so a new evaluator appears here without an edit."""
    assert tools.describe_provider()["condition_types"] == sorted(EVALUATORS_DICT)


def test_describe_provider_reads_real_operation_registries():
    from tirith.providers.json import handler as json_handler
    from tirith.providers.kubernetes import handler as k8s_handler

    assert tools.describe_provider("json")["operation_types"] == sorted(json_handler.SUPPORTED_OPS)
    assert tools.describe_provider("kubernetes")["operation_types"] == sorted(k8s_handler.SUPPORTED_OPS)


def test_terraform_plan_operation_list_has_not_drifted():
    """
    terraform_plan dispatches through an if/elif chain with no registry to import, so its
    operations are hardcoded in tools.py. This reads the handler source and fails when the two
    disagree -- which is the whole reason it is safe to hardcode them.
    """
    path = os.path.join(REPO, "src", "tirith", "providers", "terraform_plan", "handler.py")
    with open(path) as handle:
        source = handle.read()
    found = set(re.findall(r'input_type\s*==\s*"([a-z_]+)"', source))
    assert found == set(tools._TERRAFORM_PLAN_OPS), (
        "terraform_plan's operation_type values changed; update _TERRAFORM_PLAN_OPS in "
        "src/tirith/mcp/tools.py"
    )


def test_describe_provider_rejects_an_unknown_provider():
    out = tools.describe_provider("stackguardian/nope")
    assert "error" in out and out["known_providers"]


# --------------------------------------------------------------- explain_result ---


def test_explain_result_names_rule_resource_and_value():
    policy, document = _example("02-no-public-buckets")
    result = tools.evaluate(policy, document)["result"]
    out = tools.explain_result(result)
    assert out["verdict"]["outcome"] == "failed"
    assert out["failures"]
    assert any(f["resource"] for f in out["failures"]), "at least one failure should name a resource"


def test_explain_result_admits_when_a_failure_has_no_resource():
    """
    The missing-attribute case: the engine has no value to attach a resource to, so the failure
    arrives without an address. Saying so beats leaving the reader to wonder.
    """
    policy, document = _example("01-required-tags")
    result = tools.evaluate(policy, document)["result"]
    out = tools.explain_result(result)
    assert any(f["resource"] is None for f in out["failures"])
    assert "no resource address" in out["note"]


# ------------------------------------------------------- the documented traps ---
#
# Each of these is a mistake that produces a policy which looks correct and behaves wrongly.
# They were found the hard way while writing the starter pack, so they are pinned here.


def _policy(evaluator):
    return {
        "meta": {"version": "v1", "required_provider": "stackguardian/terraform_plan", "name": "n"},
        "evaluators": [evaluator],
        "eval_expression": "a",
    }


def test_lint_catches_the_attribute_path_typo():
    """An unrecognised provider_args key is ignored, so the evaluator silently reads nothing."""
    report = tools.lint_policy(
        _policy(
            {
                "id": "a",
                "provider_args": {"operation_type": "attribute", "attribute_path": "tags.Owner"},
                "condition": {"type": "IsNotEmpty"},
            }
        )
    )
    assert not report["ok"]
    assert any("terraform_resource_attribute" in p["message"] for p in report["problems"])


def test_lint_explains_how_to_negate_instead_of_NotRegexMatch():
    report = tools.lint_policy(
        _policy({"id": "a", "provider_args": {"operation_type": "attribute"}, "condition": {"type": "NotRegexMatch"}})
    )
    assert not report["ok"]
    assert any("eval_expression" in p["message"] and "!" in p["message"] for p in report["problems"])


@pytest.mark.parametrize("operation", ["jmespath", "jq_query"])
def test_lint_rejects_operations_that_do_not_ship(operation):
    """Test fixtures in this repository reference these, which makes them look supported."""
    report = tools.lint_policy(
        _policy({"id": "a", "provider_args": {"operation_type": operation}, "condition": {"type": "IsNotEmpty"}})
    )
    assert not report["ok"]


def test_lint_warns_when_error_tolerance_is_in_the_wrong_place():
    report = tools.lint_policy(
        _policy(
            {
                "id": "a",
                "provider_args": {"operation_type": "attribute"},
                "condition": {"type": "IsNotEmpty"},
                "error_tolerance": 1,
            }
        )
    )
    assert report["ok"], "misplaced error_tolerance is a warning: the policy still runs"
    assert any("inside `condition`" in p["message"] for p in report["problems"])


def test_gotchas_are_exposed_to_an_agent():
    """describe_provider carries them, so an agent gets them before writing rather than after."""
    gotchas = tools.describe_provider()["gotchas"]
    assert len(gotchas) >= 6
    joined = " ".join(gotchas)
    for token in ["terraform_resource_attribute", "error_tolerance", "NotRegexMatch", "change.after", "count", "jq_query"]:
        assert token in joined
