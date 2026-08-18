"""
The validator must accept every policy that actually works, and explain the ones that do not.

The first half matters more than the second. A validator that flags a working policy is worse
than no validator: it teaches the user to ignore it. `test_repo_fixture_policies_are_accepted`
runs it over every policy fixture in the repository -- the same files the engine's own tests
evaluate -- and requires zero errors on all of them.

No textual import here either; validate.py depends only on the engine, so this runs on CI's
Python 3.8 leg where textual cannot be installed.
"""

import json
import os

from pytest import mark

from tirith.tui import validate

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIXTURES_ROOT = os.path.join(REPO_ROOT, "tests", "providers")


def _valid_policy():
    return {
        "meta": {"version": "v1", "required_provider": "stackguardian/json"},
        "evaluators": [
            {
                "id": "check0",
                "provider_args": {"operation_type": "get_value", "key_path": "a"},
                "condition": {"type": "Equals", "value": 1},
            }
        ],
        "eval_expression": "check0",
    }


def _errors(policy):
    return [f for f in validate.check_policy(policy) if f.severity == "error"]


def _collect_policy_fixtures():
    """Every *policy*.json under tests/providers, which are known-good by construction."""
    found = []
    for dirpath, _dirnames, filenames in os.walk(FIXTURES_ROOT):
        for filename in filenames:
            if not filename.endswith(".json"):
                continue
            if "policy" not in filename and not filename.endswith(".tirith.json"):
                continue
            found.append(os.path.join(dirpath, filename))
    return sorted(found)


# Fixtures the engine itself cannot run, with the reason each was confirmed against the engine
# rather than assumed. Listed by name so a fixture becoming valid -- or a new broken one landing
# -- fails this test instead of being silently tolerated by a blanket try/except.
KNOWN_INVALID_FIXTURES = {
    # Declares `sg_workflow`, not the namespaced `stackguardian/sg_workflow` the engine
    # dispatches on. PROVIDERS_DICT has no such key, so every check fails with
    # "Provider is not found".
    "wfPolicy.json": "legacy un-namespaced required_provider",
    "policy.json:providers": "legacy un-namespaced required_provider",
    # `eval_expression` uses a single `&`. Confirmed by running it: the engine raises
    # ValueError("Unsupported operator '&' ... Use '&&' instead") and returns no result at all.
    "policy.json:fixtures": "eval_expression uses '&' which the engine rejects",
    # operation_types `jmespath` and `jq_query` appear nowhere in the engine, and no test
    # references this file. It documents an intended feature that was never implemented.
    "policy_mixed_queries.json": "uses unimplemented jmespath/jq_query operations",
}


def _fixture_key(policy_path):
    """
    Key a fixture by name, falling back to name:parent for the several files called policy.json.
    """
    name = os.path.basename(policy_path)
    qualified = f"{name}:{os.path.basename(os.path.dirname(policy_path))}"
    return qualified if qualified in KNOWN_INVALID_FIXTURES else name


@mark.passing
@mark.parametrize("policy_path", _collect_policy_fixtures())
def test_repo_fixture_policies_are_accepted(policy_path):
    """
    Every policy fixture the engine can actually run must validate clean.

    This is the check that keeps the validator honest. A validator that flags a working policy
    trains the user to ignore it, so the bar is: if the engine runs it, we do not report an
    error on it. Fixtures the engine genuinely cannot run are listed in KNOWN_INVALID_FIXTURES
    with the reason, and are asserted to still be reported.
    """
    with open(policy_path) as f:
        policy = json.load(f)

    relative = os.path.relpath(policy_path, REPO_ROOT)
    errors = _errors(policy)

    if _fixture_key(policy_path) in KNOWN_INVALID_FIXTURES:
        assert errors, f"{relative} is listed as known-invalid but validates clean; remove it from the list."
        return

    assert not errors, f"{relative} reported: " + "; ".join(str(e) for e in errors)


@mark.passing
def test_accepts_a_minimal_policy():
    assert validate.check_policy(_valid_policy()) == []


@mark.passing
def test_missing_meta_is_an_error_not_an_exception():
    """
    The engine raises AttributeError on this input; the whole point is to report it instead.
    """
    policy = _valid_policy()
    del policy["meta"]
    assert any(f.where == "meta" for f in _errors(policy))


@mark.passing
def test_non_dict_policy_is_reported():
    for junk in ([], "a string", 7, None):
        findings = validate.check_policy(junk)
        assert findings and findings[0].severity == "error"


@mark.passing
def test_unknown_provider_is_reported():
    policy = _valid_policy()
    policy["meta"]["required_provider"] = "stackguardian/nope"
    assert any("Unknown provider" in f.message for f in _errors(policy))


@mark.passing
def test_unknown_operation_is_reported():
    policy = _valid_policy()
    policy["evaluators"][0]["provider_args"]["operation_type"] = "nope"
    assert any("not supported" in f.message for f in _errors(policy))


@mark.passing
def test_missing_required_provider_arg_is_reported():
    policy = _valid_policy()
    del policy["evaluators"][0]["provider_args"]["key_path"]
    assert any(f.where.endswith("key_path") for f in _errors(policy))


@mark.passing
def test_unknown_evaluator_is_reported():
    policy = _valid_policy()
    policy["evaluators"][0]["condition"]["type"] = "AlmostEquals"
    assert any("is not an evaluator" in f.message for f in _errors(policy))


@mark.passing
def test_hyphenated_id_that_is_used_still_works():
    """
    A hyphenated id is not an error while it is referenced.

    core substitutes ids into the expression by regex before compiling, so `eval-id-1` is
    replaced by `True`/`False` and never reaches the parser. Several shipped fixtures rely on
    this. Reporting it as an error would flag working policies, so it is a warning.
    """
    policy = _valid_policy()
    policy["evaluators"][0]["id"] = "check-0"
    policy["eval_expression"] = "check-0"

    findings = validate.check_policy(policy)
    assert not [f for f in findings if f.severity == "error"]
    assert any(f.severity == "warning" and f.where.endswith(".id") for f in findings)


@mark.passing
def test_undefined_hyphenated_id_is_an_error():
    """
    Undefined is where a hyphen turns fatal: nothing substitutes it, the `-` survives to the
    parser, and core raises ValueError instead of returning a verdict.
    """
    policy = _valid_policy()
    policy["eval_expression"] = "check0 && eval-id-9"

    errors = _errors(policy)
    assert any("eval-id-9" in f.message for f in errors), errors


@mark.passing
def test_hyphenated_id_is_not_split_into_phantom_names():
    """
    A parse-first approach reads `eval-id-1` as `eval - id - 1` and invents two undefined
    names. The reference scan must resolve declared ids the way core does instead.
    """
    policy = _valid_policy()
    policy["evaluators"][0]["id"] = "eval-id-1"
    policy["eval_expression"] = "eval-id-1"

    messages = " ".join(f.message for f in validate.check_policy(policy))
    assert "'eval'" not in messages and "'id'" not in messages


@mark.passing
def test_duplicate_ids_are_reported():
    policy = _valid_policy()
    policy["evaluators"].append(dict(policy["evaluators"][0]))
    assert any("Duplicate id" in f.message for f in _errors(policy))


@mark.passing
def test_single_ampersand_is_reported():
    """
    core raises ValueError for `&`, and the README documented it in two examples, so a user can
    reach this by copying the docs. Report it before the engine runs.
    """
    policy = _valid_policy()
    policy["eval_expression"] = "check0 & check0"
    assert any("&&" in f.message for f in _errors(policy))


@mark.passing
def test_undefined_id_in_expression_is_reported():
    policy = _valid_policy()
    policy["eval_expression"] = "check0 && typo_id"
    assert any("typo_id" in f.message for f in _errors(policy))


@mark.passing
def test_unused_check_is_a_warning_not_an_error():
    """A check that runs but is not referenced still evaluates, so it must not block."""
    policy = _valid_policy()
    policy["evaluators"].append(
        {
            "id": "check1",
            "provider_args": {"operation_type": "get_value", "key_path": "b"},
            "condition": {"type": "Equals", "value": 2},
        }
    )
    findings = validate.check_policy(policy)
    assert not [f for f in findings if f.severity == "error"]
    assert any(f.severity == "warning" and "check1" in f.message for f in findings)


@mark.passing
def test_negation_counts_as_a_reference():
    """`!check0` refers to check0; a regex over the raw string would miss it."""
    policy = _valid_policy()
    policy["eval_expression"] = "!check0"
    assert validate.check_policy(policy) == []


@mark.passing
def test_contained_in_accepts_a_string():
    """
    ContainedIn branches on str (substring), list (membership) and dict (subset). Requiring a
    list here would reject a working policy, so value_kind steers the builder's widget only.
    """
    policy = _valid_policy()
    policy["evaluators"][0]["condition"] = {"type": "ContainedIn", "value": "a-substring"}
    assert not _errors(policy)


@mark.passing
def test_invalid_regex_is_reported():
    policy = _valid_policy()
    policy["evaluators"][0]["condition"] = {"type": "RegexMatch", "value": "([unclosed"}
    assert any("regular expression" in f.message for f in _errors(policy))


@mark.passing
def test_is_empty_needs_no_value():
    """IsEmpty/IsNotEmpty take no comparison value, so demanding one would be wrong."""
    policy = _valid_policy()
    policy["evaluators"][0]["condition"] = {"type": "IsNotEmpty"}
    assert validate.check_policy(policy) == []


@mark.passing
def test_null_value_is_accepted():
    """The kubernetes fixture checks `Contains: null`; absence and null are different."""
    policy = _valid_policy()
    policy["evaluators"][0]["condition"] = {"type": "Contains", "value": None}
    assert not _errors(policy)


@mark.passing
def test_unexpected_provider_arg_is_a_warning():
    """Providers ignore args they do not read, so a typo'd key runs -- it just does nothing."""
    policy = _valid_policy()
    policy["evaluators"][0]["provider_args"]["kee_path"] = "a"
    findings = validate.check_policy(policy)
    assert not [f for f in findings if f.severity == "error"]
    assert any("ignored" in f.message for f in findings)


@mark.passing
def test_terraform_plan_without_resource_changes_is_flagged():
    """The commonest input mistake: passing the binary plan, or state, instead of show -json."""
    findings = validate.check_input_document({}, "stackguardian/terraform_plan")
    assert any("resource_changes" in f.where for f in findings)


# Each malformed shape the validator recognises, as (mutation, expected text). These are the
# branches that exist *because* the engine reports them confusingly or not at all, so leaving
# them untested would leave the validator's whole reason for existing unexercised.
MALFORMED = [
    ("meta is not an object", {"meta": []}, "Must be an object"),
    ("evaluators missing", {"evaluators": None}, "Missing"),
    ("evaluators is not a list", {"evaluators": {}}, "Must be a list"),
    ("evaluator is not an object", {"evaluators": ["nope"]}, "Must be an object"),
    ("eval_expression missing", {"eval_expression": None}, "Missing"),
    ("eval_expression is not a string", {"eval_expression": 7}, "Must be a string"),
    ("eval_expression is empty", {"eval_expression": "   "}, "Empty"),
]


@mark.passing
@mark.parametrize("label,patch,expected", MALFORMED, ids=[m[0] for m in MALFORMED])
def test_malformed_policies_are_reported(label, patch, expected):
    del label
    policy = _valid_policy()
    policy.update(patch)
    # A key set to None means "absent" here, which is how these arrive from a half-written
    # document rather than from a deliberate null.
    for key, value in patch.items():
        if value is None:
            del policy[key]

    assert any(expected in f.message for f in _errors(policy)), _errors(policy)


@mark.passing
def test_a_missing_version_is_only_a_warning():
    """The engine does not read it, so it is a convention rather than a requirement."""
    policy = _valid_policy()
    del policy["meta"]["version"]

    findings = validate.check_policy(policy)
    assert not [f for f in findings if f.severity == "error"]
    assert any("version" in f.where for f in findings)


@mark.passing
def test_an_empty_evaluator_list_warns_that_nothing_is_checked():
    policy = _valid_policy()
    policy["evaluators"] = []
    policy["eval_expression"] = "x"

    assert any("checks nothing" in f.message for f in validate.check_policy(policy))


@mark.passing
def test_a_check_without_an_id_is_reported():
    policy = _valid_policy()
    del policy["evaluators"][0]["id"]

    assert any(f.where.endswith(".id") for f in _errors(policy))


@mark.passing
def test_missing_provider_args_and_condition_are_reported():
    for key in ("provider_args", "condition"):
        policy = _valid_policy()
        del policy["evaluators"][0][key]
        assert any(f.where.endswith(key) for f in _errors(policy)), key


@mark.passing
def test_provider_args_and_condition_of_the_wrong_type_are_reported():
    for key in ("provider_args", "condition"):
        policy = _valid_policy()
        policy["evaluators"][0][key] = "not an object"
        assert any("Must be an object" in f.message for f in _errors(policy)), key


@mark.passing
def test_a_value_outside_a_closed_choice_list_is_reported():
    """
    sg_workflow raises KeyError on an attribute it does not branch on, so a value outside the
    list is a policy that always errors rather than one that merely reads oddly.
    """
    policy = {
        "meta": {"version": "v1", "required_provider": "stackguardian/sg_workflow"},
        "evaluators": [
            {
                "id": "wf",
                "provider_args": {"workflow_attribute": "NoSuchField"},
                "condition": {"type": "Equals", "value": True},
            }
        ],
        "eval_expression": "wf",
    }

    assert any("is not one of" in f.message for f in _errors(policy))


@mark.passing
def test_a_single_pipe_is_reported():
    """The mirror of the `&` case: core rejects it, so say so before the engine runs."""
    policy = _valid_policy()
    policy["eval_expression"] = "check0 | check0"

    assert any("||" in f.message for f in _errors(policy))


@mark.passing
def test_a_non_integer_error_tolerance_is_reported():
    policy = _valid_policy()
    policy["evaluators"][0]["condition"]["error_tolerance"] = "two"

    assert any(f.where.endswith("error_tolerance") for f in _errors(policy))


@mark.passing
def test_infracost_input_without_projects_is_flagged():
    findings = validate.check_input_document({}, "stackguardian/infracost")
    assert any("projects" in f.where for f in findings)


@mark.passing
def test_a_single_kubernetes_object_is_flagged():
    """The provider iterates a list of manifests; one object matches no kind at all."""
    findings = validate.check_input_document({"kind": "Pod"}, "stackguardian/kubernetes")
    assert findings


@mark.passing
def test_summarize_counts_errors_and_warnings():
    policy = _valid_policy()
    policy["evaluators"][0]["provider_args"]["kee_path"] = "a"  # warning
    policy["evaluators"][0]["condition"]["type"] = "Nope"  # error

    errors, warnings = validate.summarize(validate.check_policy(policy))

    assert errors >= 1 and warnings >= 1


@mark.passing
@mark.parametrize("bad", [["stackguardian/json"], {"name": "x"}], ids=["list", "dict"])
def test_an_unhashable_provider_is_reported_not_raised(bad):
    """
    A list or an object here is unhashable, so `x not in PROVIDERS_DICT` raised TypeError
    instead of returning False -- and check_policy is called outside any try in the Playground,
    so the exception escaped and killed the app mid-edit. That is the one thing this module
    exists to prevent.

    Reachable by an ordinary mistake: the neighbouring resource_type argument really is a list.
    """
    policy = _valid_policy()
    policy["meta"]["required_provider"] = bad

    assert any("Must be a string" in f.message for f in _errors(policy))


@mark.passing
@mark.parametrize("bad", [["Equals"], {"type": "Equals"}], ids=["list", "dict"])
def test_an_unhashable_evaluator_type_is_reported_not_raised(bad):
    """The same unhashable-key hazard at condition.type."""
    policy = _valid_policy()
    policy["evaluators"][0]["condition"]["type"] = bad

    assert any("Must be a string" in f.message for f in _errors(policy))


@mark.passing
def test_exclude_resource_types_is_accepted_by_count_and_action():
    """
    terraform_plan reads exclude_resource_types once and honours it in the attribute, count and
    action branches alike. Described against attribute only, the validator told the author of a
    correct count policy that the argument "will be ignored" -- the opposite of true.
    """
    for operation, condition in (
        ("count", {"type": "GreaterThan", "value": 0}),
        ("action", {"type": "NotContains", "value": "delete"}),
    ):
        policy = {
            "meta": {"version": "v1", "required_provider": "stackguardian/terraform_plan"},
            "evaluators": [
                {
                    "id": "check",
                    "provider_args": {
                        "operation_type": operation,
                        "terraform_resource_type": "*",
                        "exclude_resource_types": ["aws_iam_policy"],
                    },
                    "condition": condition,
                }
            ],
            "eval_expression": "check",
        }

        assert validate.check_policy(policy) == [], operation


@mark.passing
def test_errors_sort_before_warnings():
    """A UI showing only the first finding must show a blocking one."""
    policy = _valid_policy()
    policy["evaluators"][0]["provider_args"]["kee_path"] = "a"  # warning
    policy["evaluators"][0]["condition"]["type"] = "Nope"  # error
    findings = validate.check_policy(policy)
    assert findings[0].severity == "error"
