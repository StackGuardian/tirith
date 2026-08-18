"""
`tirith local check`, end to end through the real CLI.

The exit-code matrix is the point of this file. Local mode is a *gate*, and the only thing that
gates is the exit code, so every branch of it is pinned here rather than inferred from the result
document.
"""

import json

from conftest import policy_with_enforcement

from tirith.cli import main
from tirith.status import ExitStatus


def test_a_failing_policy_exits_zero_by_default(workspace):
    """
    Matches `platform check`: the report appears, the job stays green. Useful while someone is
    writing their first policies, and the default a caller can rely on not changing.
    """
    workspace.policy()
    workspace.plan()

    assert main(workspace.argv()) == ExitStatus.SUCCESS
    assert workspace.result()["verdict"] == "failed"


def test_a_failing_policy_exits_three_with_fail_on_error(workspace):
    workspace.policy()
    workspace.plan()

    assert main(workspace.argv("--fail-on-error")) == ExitStatus.ERROR_POLICY_FAILED


def test_a_passing_policy_exits_zero(workspace):
    workspace.policy()
    workspace.plan(instance_type="t3.micro")

    assert main(workspace.argv("--fail-on-error")) == ExitStatus.SUCCESS
    assert workspace.result()["verdict"] == "passed"


def test_no_policies_is_a_failure_not_a_skip(workspace):
    """
    The one outcome this mode must never produce is a green result for a change nothing was
    evaluated against. Pointed at an empty directory, it fails -- and it fails whether or not
    --fail-on-error was passed, because this is a configuration error, not a policy decision.
    """
    workspace.plan()

    assert main(workspace.argv()) == ExitStatus.ERROR
    assert main(workspace.argv("--fail-on-error")) == ExitStatus.ERROR
    assert workspace.result()["verdict"] == "errored"


def test_a_policy_that_cannot_be_evaluated_fails_regardless_of_fail_on_error(workspace):
    """
    "Could not evaluate" is tool health, not a policy decision, so it ignores --fail-on-error
    exactly as an unreachable platform does in the other mode. Without this a broken policy file
    reported a green job.
    """
    workspace.policy(name="broken.tirith.json", document={"meta": {}, "evaluators": [{"nonsense": True}]})
    workspace.plan()

    assert main(workspace.argv()) == ExitStatus.ERROR

    result = workspace.result()
    assert result["policies_errored"] == 1
    assert result["policy_errors"][0]["policy"].endswith("broken.tirith.json")
    assert result["policy_errors"][0]["reason"]


def test_a_missing_input_document_fails_and_still_writes_a_report(workspace):
    """
    Both output files are written on every exit path. A front end that edits a sticky comment in
    place needs a marker-first body even here -- writing nothing is what orphaned the comment it was
    updating.
    """
    workspace.policy()
    marker = "[//]: <> (tirith-comment, tag=default)"

    status = main(workspace.argv("--comment-marker", marker))

    assert status == ExitStatus.ERROR
    assert workspace.result()["verdict"] == "errored"
    assert workspace.markdown().startswith(marker)


def test_the_failure_report_says_why_rather_than_naming_a_workflow_run(workspace):
    """
    The renderer's generic errored narrative talks about "the workflow run", which local mode does
    not have. The real reason is passed through instead.
    """
    workspace.plan()

    main(workspace.argv())
    body = workspace.markdown()

    assert "workflow run" not in body
    assert "no policy files found" in body


def test_the_marker_is_the_first_line_of_a_normal_report(workspace):
    """Stickiness depends on it: a caller finds its own note by matching the marker as a prefix."""
    workspace.policy()
    workspace.plan()
    marker = "[//]: <> (tirith-comment, tag=envs-prod)"

    main(workspace.argv("--comment-marker", marker))

    assert workspace.markdown().startswith(marker)


def test_an_advisory_policy_warns_instead_of_failing(workspace):
    """`meta.enforcement` downgrades a failing policy, matching the platform's onFail handling."""
    workspace.policy(document=policy_with_enforcement("soft_mandatory"))
    workspace.plan()

    assert main(workspace.argv("--fail-on-error")) == ExitStatus.SUCCESS
    assert workspace.result()["verdict"] == "warned"


def test_an_unrecognised_enforcement_gates_and_says_so(workspace):
    """
    An unlabelled or mislabelled policy must gate, not slip through -- but the reader has to be told,
    or a typo in `enforcement` silently becomes policy. The notice is in the document as well as the
    log so a front end can annotate without scraping stderr.
    """
    workspace.policy(document=policy_with_enforcement("sort-of-important"))
    workspace.plan()

    assert main(workspace.argv("--fail-on-error")) == ExitStatus.ERROR_POLICY_FAILED

    warnings = workspace.result()["policy_warnings"]
    assert len(warnings) == 1
    assert "sort-of-important" in warnings[0]


def test_a_correctly_labelled_blocking_policy_raises_no_warning(workspace):
    """
    `hard_mandatory` is what tirith's own golden test pins, so treating it as unrecognised fired the
    notice on essentially every failing run.
    """
    workspace.policy(document=policy_with_enforcement("hard_mandatory"))
    workspace.plan()

    main(workspace.argv())

    assert workspace.result()["policy_warnings"] == []


def test_the_masked_document_is_what_gets_evaluated(workspace):
    """
    Masking matters even though nothing is uploaded: evaluator messages embed the values they
    compared, and those messages are copied verbatim into whatever note the caller posts. An
    unmasked local run publishes plan values to a code host.
    """
    workspace.policy()
    workspace.plan(secret="hunter2-should-never-appear")

    main(workspace.argv())

    assert "hunter2-should-never-appear" not in json.dumps(workspace.result())
    assert "hunter2-should-never-appear" not in workspace.markdown()


def test_infracost_path_is_accepted_and_reported_as_ignored(workspace, capsys):
    """
    Cost policies need a second document, which this mode does not evaluate. Saying so beats
    evaluating the plan and reporting a cost policy as unevaluated with no explanation.
    """
    workspace.policy()
    workspace.plan()

    main(workspace.argv("--infracost-path", str(workspace.root / "infracost.json")))

    assert "--infracost-path is ignored in local mode" in capsys.readouterr().err


def test_local_check_with_no_subcommand_prints_help(capsys):
    assert main(["local"]) == ExitStatus.SUCCESS
    assert "tirith local" in capsys.readouterr().out
