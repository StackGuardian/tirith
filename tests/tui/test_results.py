"""
The results model must read what the engine really emits, including the parts it omits.

Most of these run the engine over repository fixtures rather than asserting against
hand-written dicts, because the shape being modelled is the engine's, and a hand-written
sample is exactly where a wrong assumption survives. The `meta` block in particular varies:
terraform_plan populates it with the whole resource_change, infracost sets it to None, and
some json-provider results omit the key entirely.

No textual import; this runs on CI's Python 3.8 leg.
"""

import json
import os

from pytest import mark

from tirith.core.core import start_policy_evaluation_from_dict
from tirith.tui import results

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TF_FIXTURES = os.path.join(REPO_ROOT, "tests", "providers", "terraform_plan", "fixtures")


def _run(policy_path, input_path):
    with open(policy_path) as f:
        policy = json.load(f)
    with open(input_path) as f:
        input_data = json.load(f)
    return start_policy_evaluation_from_dict(policy, input_data)


def _tf_report(policy_name, input_name):
    return results.parse_report(_run(os.path.join(TF_FIXTURES, policy_name), os.path.join(TF_FIXTURES, input_name)))


@mark.passing
def test_parses_a_real_terraform_run():
    report = _tf_report("policy_costcenter_tags.json", "input_costcenter_tags.json")

    assert report.checks
    assert report.verdict == results.PASSED
    assert report.counts[results.PASSED] == len(report.checks)


@mark.passing
def test_resource_detail_is_recovered_from_meta():
    """
    The whole point of the Explorer: name the resource each result came from.

    The pretty printer prints only the message, so this detail exists in the document today
    and has no way to reach the user.
    """
    report = _tf_report("policy_costcenter_tags.json", "input_costcenter_tags.json")

    resources = [r.resource for check in report.checks for r in check.results]
    assert resources, "fixture produced no results"

    # This policy matches on '*', so it spans several resource types -- which is exactly the
    # case the Explorer exists for: the printed messages are indistinguishable from each other
    # ("`\"product-456\"` is not empty") and only the address says which resource each is.
    addresses = sorted(r.address for r in resources)
    assert addresses == ["aws_instance.web", "aws_s3_bucket.logs", "aws_vpc.main"]
    assert all(r.resource_type for r in resources), "every matched resource should name its type"


@mark.passing
def test_missing_meta_yields_an_empty_ref_not_an_error():
    """
    infracost sets meta to None and some json results omit the key. Both must parse.
    """
    report = results.parse_report(
        _run(
            os.path.join(REPO_ROOT, "tests", "providers", "infracost", "policy.json"),
            os.path.join(REPO_ROOT, "tests", "providers", "infracost", "input.json"),
        )
    )

    for check in report.checks:
        for result in check.results:
            assert result.resource.is_empty
            assert result.resource.label == ""


@mark.passing
def test_skipped_is_not_counted_as_passed():
    """
    The engine is careful that a skipped check is not a pass; so is this model.
    """
    report = results.parse_report(
        {
            "evaluators": [
                {"id": "a", "passed": None, "result": [{"passed": None, "message": "skipped"}]},
                {"id": "b", "passed": True, "result": [{"passed": True, "message": "ok"}]},
            ],
            "final_result": None,
            "errors": [],
        }
    )

    assert report.counts == {results.PASSED: 1, results.FAILED: 0, results.SKIPPED: 1}
    assert report.verdict == results.SKIPPED


@mark.passing
def test_absent_final_result_is_distinct_from_none():
    """
    `final_result: None` means everything was skipped. No key at all means the policy could
    not be loaded. The CLI gates differently on each, so the model must not conflate them.
    """
    skipped = results.parse_report({"evaluators": [], "final_result": None, "errors": []})
    errored = results.parse_report({"errors": ["Variables not found: env"]})

    assert skipped.verdict == results.SKIPPED
    assert errored.verdict == "errored"
    assert errored.errors == ["Variables not found: env"]


@mark.passing
def test_garbage_input_does_not_raise():
    """The Explorer can be pointed at any file; it must report, not crash."""
    for junk in (None, [], "text", 3):
        report = results.parse_report(junk)
        assert report.checks == []
        assert report.verdict == "errored"


@mark.passing
def test_action_summary_names_replacement_order():
    """
    delete-then-create means downtime and create-then-delete does not, so the two orderings
    must not render identically.
    """
    destroy_first = results.ResourceRef(actions=("delete", "create"))
    create_first = results.ResourceRef(actions=("create", "delete"))

    assert destroy_first.action_summary != create_first.action_summary
    assert "destroy first" in destroy_first.action_summary
    assert "create first" in create_first.action_summary


@mark.passing
def test_action_summary_reads_plainly_for_simple_actions():
    assert results.ResourceRef(actions=("create",)).action_summary == "create"
    assert results.ResourceRef(actions=("delete",)).action_summary == "destroy"
    assert results.ResourceRef(actions=("no-op",)).action_summary == "no change"
    assert results.ResourceRef(actions=()).action_summary == ""


@mark.passing
def test_attribute_changes_lists_only_what_changed():
    """
    A plan's `after` block repeats every attribute of the resource. Showing all of them buries
    the ones that moved, which is the reason this filters.
    """
    meta = {
        "change": {
            "actions": ["update"],
            "before": {"instance_type": "t2.micro", "ami": "ami-1", "tags": {"a": 1}},
            "after": {"instance_type": "t3.micro", "ami": "ami-1", "tags": {"a": 1}},
        }
    }

    changes = results.attribute_changes(meta)

    assert [c.name for c in changes] == ["instance_type"]
    assert changes[0].before == "t2.micro"
    assert changes[0].after == "t3.micro"


@mark.passing
def test_attribute_changes_flags_values_unknown_until_apply():
    """
    An attribute that is computed at apply time is not the same as one set to null, and
    rendering it as null would say something false about the plan.
    """
    meta = {
        "change": {
            "actions": ["update"],
            "before": {"arn": "arn:old"},
            "after": {},
            "after_unknown": {"arn": True},
        }
    }

    (change,) = results.attribute_changes(meta)

    assert change.name == "arn"
    assert change.after_unknown is True


@mark.passing
def test_attribute_changes_is_empty_without_a_before_after_pair():
    """A create has no before, so there is no diff to show; the caller shows `after` instead."""
    assert results.attribute_changes({"change": {"actions": ["create"], "before": None, "after": {"a": 1}}}) == []
    assert results.attribute_changes({}) == []
    assert results.attribute_changes(None) == []


@mark.passing
def test_real_destroy_plan_is_summarized_as_destroy():
    """Checked against a real plan fixture rather than a hand-built change block."""
    report = _tf_report("policy_s3_destroy.json", "input_s3_destroy.json")

    actions = [r.resource.action_summary for check in report.checks for r in check.results if r.resource.actions]
    assert any("destroy" in a for a in actions), actions


@mark.passing
def test_check_summary_counts_its_results():
    report = _tf_report("policy_costcenter_tags.json", "input_costcenter_tags.json")
    check = report.checks[0]

    assert check.counts[results.PASSED] == len(check.results)
    assert "passed" in check.summary


@mark.passing
def test_failing_results_are_reachable_directly():
    """The Explorer opens on failures, so getting to them must not require walking every check."""
    report = results.parse_report(
        {
            "evaluators": [
                {
                    "id": "a",
                    "passed": False,
                    "result": [{"passed": False, "message": "no"}, {"passed": True, "message": "yes"}],
                }
            ],
            "final_result": False,
            "errors": [],
        }
    )

    failing = list(report.iter_failing_results())

    assert len(failing) == 1
    assert failing[0].message == "no"
