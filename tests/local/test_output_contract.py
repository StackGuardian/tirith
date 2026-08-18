"""
The two modes produce one document shape.

Both front ends -- the GitHub Action and the GitLab CI component -- read `--output-json` and turn it
into comments, statuses and job outputs. If the key set differs by mode, every consumer has to write
two parsers, and the one that forgets reports the wrong thing on the mode it was not tested against.

So the contract is: **every key exists in every mode.** A key with no meaning on a path is None (or
[] for the lists), never omitted and never invented. That is enforced by construction --
`report.result_document` builds both -- and pinned here, because construction is only a guarantee
while both callers keep using it.
"""

import json

from conftest import POLICY, plan

from tirith.cli import main
from tirith.platform import report
from tirith.status import ExitStatus

# Keys read by the GitHub Action and the GitLab component. Adding one is fine; removing or renaming
# one breaks a released consumer, which is what this list is for.
CONSUMER_KEYS = {
    "mode",
    "status",
    "verdict",
    "counts",
    "headline",
    "policy_results",
    "wfrun_id",
    "wfrun_url",
    "monthly_cost",
    "archive_key",
    "source_packed",
    "source_skipped_reason",
    "policies_evaluated",
    "policies_errored",
    "policy_path",
    "policy_errors",
    "policy_warnings",
}

COUNT_KEYS = {"passed", "failed", "warned", "approval_required", "skipped", "unknown"}


def _platform_document():
    """What a platform run produces, without needing a platform."""
    return report.result_document(
        "platform",
        "COMPLETED",
        {"some-policy": [{"rule_name": "a rule", "result": report.PASS}]},
        wfrun_id="abc123",
        wfrun_url="https://app.stackguardian.io/...",
        monthly_cost=12.5,
        archive_key="orgs/acme/wfs/K/artifacts/bundle.tar.gz",
        source_packed=True,
    )


def _local_document(workspace):
    workspace.policy()
    workspace.plan()
    main(workspace.argv())
    return workspace.result()


def test_both_modes_carry_the_same_keys(workspace):
    platform = _platform_document()
    local = _local_document(workspace)

    assert set(platform) == set(local)
    assert set(local) == CONSUMER_KEYS
    assert set(platform["counts"]) == set(local["counts"]) == COUNT_KEYS


def test_the_mode_discriminator_is_the_mode(workspace):
    """
    Consumers should read `mode` rather than infer it from which keys are populated -- inference is
    what makes a new key a breaking change.
    """
    assert _platform_document()["mode"] == "platform"
    assert _local_document(workspace)["mode"] == "local"


def test_local_mode_invents_no_run(workspace):
    """
    A fabricated wfrun_url would render as a link to a run that does not exist. None is the honest
    value, and consumers already guard on it.
    """
    local = _local_document(workspace)

    assert local["wfrun_id"] is None
    assert local["wfrun_url"] is None
    assert local["archive_key"] is None
    assert local["monthly_cost"] is None


def test_local_mode_reports_no_source_without_claiming_a_reason(workspace):
    """
    `source_skipped_reason` stays None rather than a sentinel like "not_applicable". A consumer's
    "the terraform source was not uploaded" warning keys on truthiness, so a sentinel would fire it
    on every local run -- about an upload local mode never attempts.
    """
    local = _local_document(workspace)

    assert local["source_packed"] is False
    assert local["source_skipped_reason"] is None


def test_platform_mode_leaves_the_local_only_keys_empty(workspace):
    platform = _platform_document()

    assert platform["policies_evaluated"] is None
    assert platform["policies_errored"] is None
    assert platform["policy_path"] is None
    assert platform["policy_errors"] == []
    assert platform["policy_warnings"] == []


def test_the_document_is_json_serialisable_in_both_modes(workspace):
    """
    It is written with json.dump. A tuple or a set slipping into `policy_errors` would fail at the
    end of a long run, having already done the work.
    """
    json.dumps(_platform_document())
    json.dumps(_local_document(workspace))


def test_a_run_of_nothing_but_skips_fails_rather_than_passing(workspace):
    """
    The flat surface has always treated `final_result is None` -- every check swallowed by its
    error_tolerance -- as a failure rather than a pass: nothing was examined, so green would be a lie.
    Extending it to many policies must not quietly reverse that, which is what would have happened had
    the aggregate verdict been taken from `report.verdict` alone.

    This is a deliberate difference from `platform check`, which counts skips separately and reports
    them as a pass. Both readings are defensible; a single surface disagreeing with itself depending on
    how many policies you pointed it at is not.
    """
    # A policy naming a resource type this document does not contain, with the error_tolerance that
    # turns "not found" into a skip rather than a failure.
    document = json.loads(json.dumps(POLICY))
    document["evaluators"][0]["provider_args"]["terraform_resource_type"] = "aws_nonexistent"
    document["evaluators"][0]["condition"]["error_tolerance"] = 2
    workspace.policy(document=document)
    workspace.plan()

    assert main(workspace.argv()) == ExitStatus.ERROR

    result = workspace.result()
    assert result["verdict"] == "errored"
    assert result["counts"]["skipped"] == 1
    assert "nothing was evaluated" in workspace.markdown()

    # The reducer itself still answers `passed` for an all-skipped set -- that is platform mode's
    # answer and it is not changed here. The difference is made by this path, deliberately.
    counts, _ = report.summarize({"p": [{"rule_name": "r", "skip": True}]})
    assert report.verdict(counts, "COMPLETED") == "passed"


def test_the_platform_failure_report_is_a_full_document_with_the_reason(tmp_path):
    """
    `platform check` used to return from its error paths having written nothing, so a caller editing a
    sticky comment in place fell through to a marker-less body of its own -- which, PATCHed over a
    good comment, orphaned it permanently. Both files are now written on that path too, in the same
    shape as every other document, carrying the reason rather than a generic narrative about a
    workflow run.
    """
    from tirith.platform import check

    class Opts:
        output_json = str(tmp_path / "out.json")
        output_markdown = str(tmp_path / "out.md")
        comment_marker = "[//]: <> (tirith-comment, tag=default)"
        markdown_limit = 60000
        sha = None

    result = check.write_failure_report(Opts, "the API could not be reached")

    assert set(result) == CONSUMER_KEYS
    assert result["mode"] == "platform"
    assert result["verdict"] == "errored"
    assert result["policy_errors"] == [{"policy": None, "reason": "the API could not be reached"}]

    with open(Opts.output_markdown) as f:
        body = f.read()
    assert body.startswith(Opts.comment_marker)
    assert "the API could not be reached" in body
    assert "workflow run finished" not in body


def test_the_platform_failure_report_keeps_a_run_it_already_recorded(tmp_path):
    """
    The pre-poll write records the run id precisely so a timeout leaves the run discoverable.
    Overwriting it with nulls on the way out would throw away the only link to the run that timed out.
    """
    from tirith.platform import check

    class Opts:
        output_json = str(tmp_path / "out.json")
        output_markdown = None
        comment_marker = None
        markdown_limit = 60000
        sha = None

    with open(Opts.output_json, "w") as f:
        json.dump({"wfrun_id": "wfrun-1", "wfrun_url": "https://app.stackguardian.io/run/1"}, f)

    result = check.write_failure_report(Opts, "timed out waiting for the run")

    assert result["wfrun_id"] == "wfrun-1"
    assert result["wfrun_url"] == "https://app.stackguardian.io/run/1"
