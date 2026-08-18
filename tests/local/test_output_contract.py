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


def test_every_skipped_policy_still_reports_a_verdict_of_passed(workspace):
    """
    A deliberate divergence, recorded rather than fixed here.

    A policy whose every check was skipped (`final_result` is None) counts as SKIPPED, and a run of
    nothing-but-skips reports `passed` -- matching platform mode, which also counts skips separately
    rather than failing on them. The *flat* surface disagrees: `tirith -policy-path ... -input-path
    ... --fail-on-error` exits 1 for the same policy, on the grounds that "nothing ran" is not a pass
    (see tests/cli/test_local_gating.py).

    Both readings are defensible -- the policies genuinely did not apply, and the report says "N
    skipped" rather than hiding it -- so this is pinned to make the inconsistency visible instead of
    letting either surface drift into the other by accident. It needs a decision across all three
    surfaces, not a quiet change in one.
    """
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
