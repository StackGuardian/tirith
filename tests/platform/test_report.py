"""
Tests for verdict computation and comment rendering.

The verdict mapping is the part worth pinning hardest: every path that does not produce a real
"everything passed" must stay distinguishable from one that does, and must never map to a green
required check.
"""

import os
import sys


from tirith.platform import report as render


def _results(result="FAIL", **rule_overrides):
    rule = {
        "rule_name": "ingress-cidr",
        "result": result,
        "evaluations": {
            "fails": [
                {
                    "id": "check1",
                    "result": [
                        {
                            "passed": False,
                            "message": "`0.0.0.0/0` is contained in `cidr_blocks`",
                            "meta": {"address": "module.net.aws_security_group.web"},
                        }
                    ],
                }
            ]
        },
    }
    rule.update(rule_overrides)
    return {"no-public-ingress": [rule]}


# --- summarize ---------------------------------------------------------------------------------


def test_summarize_counts_and_extracts_detail():
    counts, findings = render.summarize(_results())

    assert counts["FAIL"] == 1
    assert findings[0]["policy_id"] == "no-public-ingress"
    assert findings[0]["messages"] == ["`0.0.0.0/0` is contained in `cidr_blocks`"]
    assert findings[0]["resources"] == ["module.net.aws_security_group.web"]


def test_summarize_counts_skipped_separately_from_passed():
    """Reporting a skipped control as passing would be a quiet inaccuracy."""
    counts, findings = render.summarize({"p": [{"rule_name": "r", "skip": True}]})

    assert counts["SKIPPED"] == 1
    assert counts["PASS"] == 0
    assert findings[0]["result"] == "SKIPPED"


def test_summarize_surfaces_engine_errors_distinctly():
    """
    A malformed policy must not read as a policy violation. Prefixing makes it obvious in the
    comment that the engine, not the infrastructure, is the problem.
    """
    results = {"p": [{"rule_name": "r", "result": "FAIL", "evaluations": {"fails": [{"exec_err": "bad op"}]}}]}

    _, findings = render.summarize(results)

    assert findings[0]["messages"] == ["engine: bad op"]


def test_summarize_handles_providers_without_resource_addresses():
    """Only terraform_plan populates meta; json/kubernetes set it to None."""
    results = {
        "p": [
            {
                "rule_name": "r",
                "result": "FAIL",
                "evaluations": {"fails": [{"id": "c", "result": [{"message": "no", "meta": None}]}]},
            }
        ]
    }

    _, findings = render.summarize(results)

    assert findings[0]["resources"] == []
    assert findings[0]["messages"] == ["no"]


def test_summarize_tolerates_empty_and_none():
    assert render.summarize(None)[0]["FAIL"] == 0
    assert render.summarize({})[1] == []


# --- verdict -----------------------------------------------------------------------------------


def test_verdict_failed_when_any_policy_fails():
    counts, _ = render.summarize(_results("FAIL"))
    assert render.verdict(counts, "COMPLETED") == "failed"


def test_verdict_warned_for_a_warning():
    counts, _ = render.summarize(_results("WARN"))
    assert render.verdict(counts, "COMPLETED") == "warned"


def test_verdict_approval_required_outranks_warned():
    """
    A rule result of APPROVAL_REQUIRED means its author wrote `onFail: APPROVAL_REQUIRED`. The
    policy-only step records that without pausing the run, so the run comes back COMPLETED and only
    the counts carry the intent.

    Folding it into `warned` was wrong: `warned` maps to a `neutral` check, which SATISFIES a
    required status check, so a policy demanding human sign-off silently did not block. Caught by a
    live run against a real APPROVAL_REQUIRED policy.
    """
    counts, _ = render.summarize(_results("APPROVAL_REQUIRED"))

    assert render.verdict(counts, "COMPLETED") == "approval-required"


def test_verdict_failed_outranks_approval_required():
    """A hard failure is the more urgent signal when a run has both."""
    counts = {"FAIL": 1, "APPROVAL_REQUIRED": 1}

    assert render.verdict(counts, "COMPLETED") == "failed"


def test_verdict_passed_only_when_a_policy_actually_passed():
    counts, _ = render.summarize(_results("PASS"))
    assert render.verdict(counts, "COMPLETED") == "passed"


def test_verdict_errored_for_a_non_completed_run():
    """An ERRORED or CANCELLED run produced no verdict; that is not a pass."""
    counts, _ = render.summarize(_results("PASS"))
    for status in ("ERRORED", "CANCELLED", "RUNNING", None):
        assert render.verdict(counts, status) == "errored", status


def test_verdict_distinguishes_no_policies_from_passed():
    """
    A run with nothing in scope is reported as such rather than as a clean bill of health -- the
    most likely cause is a policy scoped to the wrong workflow group.
    """
    assert render.verdict({}, "COMPLETED") == "no-policies"


def test_verdict_approval_required_is_not_an_error():
    """
    A run resting at APPROVAL_REQUIRED finished its evaluation; a human now has to act. Reporting
    it as `errored` would blame the tool for a working evaluation -- and the poller now stops
    there rather than spinning to its timeout.
    """
    counts, _ = render.summarize(_results("APPROVAL_REQUIRED"))

    assert render.verdict(counts, "APPROVAL_REQUIRED") == "approval-required"


# --- rendering ---------------------------------------------------------------------------------


def test_markdown_starts_with_the_marker_when_one_is_given():
    """
    The marker is opaque to this module -- GitHub's sticky-comment marker is one caller's choice --
    but when supplied it must be line 1, so the caller can find the document again.
    """
    marker = "[//]: <> (tirith-comment, tag=envs-prod)"
    body = render.render_markdown(_results(), "COMPLETED", "https://app.example/run", marker=marker)

    assert body.split("\n")[0] == marker


def test_markdown_has_no_marker_line_by_default():
    """This module is VCS-agnostic: nothing is prepended unless the caller asks for it."""
    body = render.render_markdown(_results(), "COMPLETED", "https://app.example/run")

    assert not body.startswith("[//]")
    assert body.lstrip().startswith("## ")


def test_comment_includes_table_detail_and_run_link():
    body = render.render_markdown(_results(), "COMPLETED", "https://app.example/run")

    assert "| Policy | Rule | Resource |" in body
    assert "`no-public-ingress`" in body
    assert "`0.0.0.0/0` is contained in `cidr_blocks`" in body
    assert "module.net.aws_security_group.web" in body
    assert "https://app.example/run" in body


def test_comment_explains_an_errored_run():
    body = render.render_markdown({}, "ERRORED", "https://app.example/run")

    assert "could not evaluate" in body.lower()
    assert "ERRORED" in body


def test_comment_truncates_below_the_github_limit_keeping_the_table():
    """
    GitHub rejects a body over 65536 characters with a 422. Detail sections go first; the summary
    table is what a reviewer scans, so it must survive.
    """
    results = {
        f"policy-{i}": [
            {
                "rule_name": f"rule-{i}",
                "result": "FAIL",
                "evaluations": {
                    "fails": [
                        {
                            "id": f"check-{j}",
                            "result": [
                                {
                                    "message": "x" * 400,
                                    "meta": {"address": f"aws_instance.i{j}"},
                                }
                            ],
                        }
                        for j in range(20)
                    ]
                },
            }
        ]
        for i in range(60)
    }

    body = render.render_markdown(results, "COMPLETED", "https://app.example/run", limit=20000)

    assert len(body) <= 20000
    assert "| Policy | Rule | Resource |" in body, "the summary table must survive truncation"
    assert "more finding" in body or "truncated" in body


def test_strip_marker_removes_it_for_targets_that_have_no_use_for_it():
    """A check-run summary, for instance: the marker only means something on an issue comment."""
    marker = "[//]: <> (tirith-comment, tag=default)"
    body = render.render_markdown(_results(), "COMPLETED", "https://app.example/run", marker=marker)

    summary = render.strip_marker(body)

    assert "[//]: <>" not in summary
    assert "no-public-ingress" in summary


def test_headline_reports_each_nonzero_bucket():
    counts = {"FAIL": 2, "WARN": 1, "APPROVAL_REQUIRED": 3, "PASS": 9, "SKIPPED": 1}

    assert render.headline(counts, "failed") == "Tirith — 2 failed, 3 need approval, 1 warned, 9 passed, 1 skipped"
