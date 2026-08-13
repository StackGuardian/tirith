"""
Every bundled example must load, validate and evaluate.

The examples are the first thing a new user runs, so a broken one is worse than a missing
one. These assert the whole path: the files parse, the validator accepts them, the engine
evaluates them, and each produces the verdict its `about.md` claims.

The verdicts are pinned deliberately. Several examples exist to *fail* -- that is how they
teach -- so an example silently flipping to passing would quietly destroy the lesson without
breaking anything else.

No textual import; this runs on CI's Python 3.8 leg.
"""

import json

from pytest import mark

from tirith.core.core import start_policy_evaluation_from_dict
from tirith.providers import PROVIDERS_DICT
from tirith.tui import examples, results, validate

# What each example is supposed to demonstrate. An example whose verdict moves is either a
# broken example or a changed engine; either way it should be looked at, not absorbed.
EXPECTED_VERDICTS = {
    "01-required-tags": results.FAILED,
    "02-no-public-buckets": results.FAILED,
    "03-cost-ceiling": results.PASSED,
    "04-block-destroy": results.FAILED,
    "05-kubernetes-probes": results.FAILED,
}

ALL_EXAMPLES = examples.load_examples()
EXAMPLE_KEYS = [e.key for e in ALL_EXAMPLES]


@mark.passing
def test_examples_are_discovered():
    assert EXAMPLE_KEYS, "no examples were found; the examples/ directory may not have shipped"
    assert set(EXAMPLE_KEYS) == set(
        EXPECTED_VERDICTS
    ), "the set of bundled examples changed; update EXPECTED_VERDICTS with what the new one demonstrates"


@mark.passing
@mark.parametrize("example", ALL_EXAMPLES, ids=EXAMPLE_KEYS)
def test_example_declares_a_real_provider(example):
    assert example.provider in PROVIDERS_DICT, f"{example.key} names provider '{example.provider}'"


@mark.passing
@mark.parametrize("example", ALL_EXAMPLES, ids=EXAMPLE_KEYS)
def test_example_policy_validates_clean(example):
    """An example that trips our own validator would teach the wrong thing."""
    errors = [f for f in validate.check_policy(example.policy) if f.severity == "error"]
    assert not errors, f"{example.key}: " + "; ".join(str(e) for e in errors)


@mark.passing
@mark.parametrize("example", ALL_EXAMPLES, ids=EXAMPLE_KEYS)
def test_example_evaluates_to_its_documented_verdict(example):
    report = results.parse_report(start_policy_evaluation_from_dict(example.policy, example.input_document))

    assert (
        report.verdict == EXPECTED_VERDICTS[example.key]
    ), f"{example.key} evaluated to {report.verdict}, expected {EXPECTED_VERDICTS[example.key]}"


@mark.passing
@mark.parametrize("example", ALL_EXAMPLES, ids=EXAMPLE_KEYS)
def test_example_produces_results_not_just_a_verdict(example):
    """
    A policy can reach a verdict having evaluated nothing -- every check erroring out reads as
    a failure. An example must actually exercise its input.
    """
    report = results.parse_report(start_policy_evaluation_from_dict(example.policy, example.input_document))

    assert report.checks, f"{example.key} produced no checks"
    assert any(check.results for check in report.checks), f"{example.key} produced no results"


@mark.passing
@mark.parametrize("example", ALL_EXAMPLES, ids=EXAMPLE_KEYS)
def test_example_has_an_explanation(example):
    """about.md is the teaching half; its first line is the picker's one-line summary."""
    assert example.summary, f"{example.key} has no summary line in about.md"
    assert len(example.about.splitlines()) > 3, f"{example.key} has no body in about.md"


@mark.passing
@mark.parametrize("example", ALL_EXAMPLES, ids=EXAMPLE_KEYS)
def test_example_round_trips_through_json(example):
    """The playground hands these to an editor as text, so they must survive the trip."""
    assert json.loads(example.policy_json) == example.policy
    assert json.loads(example.input_json) == example.input_document


@mark.passing
def test_titles_are_human_readable():
    """The numeric prefix orders the list; it should not show up in the UI."""
    for example in ALL_EXAMPLES:
        assert not example.title[0].isdigit(), f"{example.key} renders as '{example.title}'"


@mark.passing
def test_terraform_examples_carry_resource_addresses():
    """
    The terraform examples are the ones that demonstrate resource-level detail, so they must
    actually produce it -- that is the feature they exist to show.
    """
    for example in ALL_EXAMPLES:
        if example.provider != "stackguardian/terraform_plan":
            continue
        report = results.parse_report(start_policy_evaluation_from_dict(example.policy, example.input_document))
        addresses = [r.resource.address for check in report.checks for r in check.results if r.resource.address]
        assert addresses, f"{example.key} produced no resource addresses"


@mark.passing
def test_lookup_by_key():
    assert examples.example_by_key(EXAMPLE_KEYS[0]) is not None
    assert examples.example_by_key("no-such-example") is None
