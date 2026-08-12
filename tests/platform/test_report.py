"""
Tests for verdict computation and comment rendering.

The verdict mapping is the part worth pinning hardest: every path that does not produce a real
"everything passed" must stay distinguishable from one that does, and must never map to a green
required check.
"""

import os
import re
import sys

import pytest


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


def test_verdict_approval_required_warns_rather_than_gating():
    """
    A rule result of APPROVAL_REQUIRED means its author wrote `onFail: APPROVAL_REQUIRED`. For these
    runs there is nothing to approve: the step exits 0, the run reaches COMPLETED, and an approval
    is only ever engaged on exit 11 and never on the last step -- of which a policy-only run has
    exactly one. So it warns, deliberately, until a real gate exists.
    """
    counts, _ = render.summarize(_results("APPROVAL_REQUIRED"))

    assert render.verdict(counts, "COMPLETED") == "warned"


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


def test_a_run_paused_by_the_platform_warns_when_it_produced_results():
    """
    A run resting at APPROVAL_REQUIRED evaluated something before it paused. Reporting it as
    `errored` would blame the tool for a working evaluation -- and the poller stops there rather
    than spinning to its timeout.
    """
    counts, _ = render.summarize(_results("PASS"))

    assert render.verdict(counts, "APPROVAL_REQUIRED") == "warned"


def test_a_run_paused_before_it_evaluated_anything_is_an_error():
    """
    The one thing that must never happen: green, or even amber, for a run that produced no verdict.
    A paused run with no results has not evaluated the code.
    """
    assert render.verdict({}, "APPROVAL_REQUIRED") == "errored"


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


# --- cost line ----------------------------------------------------------------------------------


def test_cost_line_shows_the_monthly_total():
    assert "39.80 USD" in "\n".join(render.render_cost({"totalMonthlyCost": "39.8", "currency": "USD"}))


def test_cost_line_shows_the_delta_from_this_change():
    """Infracost fills the diff from the plan's prior state -- the number a reviewer wants."""
    line = "\n".join(render.render_cost({"totalMonthlyCost": "120.5", "diffTotalMonthlyCost": "39.8"}))

    assert "120.50" in line
    assert "+39.80 from this change" in line


def test_a_cost_decrease_reads_as_a_decrease():
    line = "\n".join(render.render_cost({"totalMonthlyCost": "10", "diffTotalMonthlyCost": "-5.25"}))

    assert "−5.25 from this change" in line


def test_a_zero_delta_is_omitted_rather_than_shown_as_plus_zero():
    line = "\n".join(render.render_cost({"totalMonthlyCost": "10", "diffTotalMonthlyCost": "0"}))

    assert "from this change" not in line


def test_a_zero_cost_is_still_reported():
    """Silence would be indistinguishable from 'this change costs nothing'."""
    assert "0.00" in "\n".join(render.render_cost({"totalMonthlyCost": "0"}))


def test_a_failed_estimate_says_so():
    line = "\n".join(render.render_cost({"error": "failed to perform infrastructure cost estimation"}))

    assert "unavailable" in line


def test_no_estimate_renders_nothing():
    assert render.render_cost(None) == []
    assert render.render_cost({}) == []


def test_the_cost_appears_in_the_comment_body():
    body = render.render_markdown(
        {"p": [{"rule_name": "r", "result": "PASS"}]},
        "COMPLETED",
        "https://dash.example/run",
        cost_breakdown={"totalMonthlyCost": "39.8", "currency": "USD"},
    )

    assert "39.80 USD" in body


def test_the_cost_survives_truncation_of_a_long_findings_list():
    """A wall of findings must not push the cost line out of the comment."""
    results = {
        f"policy-{i}": [
            {
                "rule_name": f"rule-{i}",
                "result": "FAIL",
                "evaluations": {"fails": [{"result": [{"message": "x" * 400}]}]},
            }
        ]
        for i in range(60)
    }

    body = render.render_markdown(
        results,
        "COMPLETED",
        "https://dash.example/run",
        limit=3000,
        cost_breakdown={"totalMonthlyCost": "39.8"},
    )

    assert len(body) <= 3000
    assert "39.80" in body


# --- checkov findings ---------------------------------------------------------------------------


def _checkov_rule(fails):
    return {
        "rule_name": "Policy-Rule-1",
        "source_config_kind": "SG_INTERNAL_P2",
        "result": "FAIL",
        "evaluations": {"fails": fails},
    }


def test_checkov_findings_are_rendered():
    """
    Checkov entries are {"description", "keys"}, not tirith's list under "result". Reading only the
    tirith shape rendered a dozen real findings as an empty <details> block -- in the one place a
    reviewer looks. Taken verbatim from QA run iqkxb26uzi1n.
    """
    body = render.render_markdown(
        {
            "best-practices": [
                _checkov_rule(
                    [
                        {
                            "description": "Ensure that detailed monitoring is enabled for EC2 instances",
                            "keys": ["aws_instance.app.monitoring"],
                        },
                    ]
                )
            ]
        },
        "COMPLETED",
        "https://dash.example/run",
    )

    assert "Ensure that detailed monitoring is enabled for EC2 instances" in body


def test_a_checkov_key_is_reduced_to_its_resource_address():
    """The attribute suffix is what the check inspected; the address is what a reviewer navigates by."""
    _messages, resources = render._extract_detail(
        _checkov_rule(
            [
                {
                    "description": "Ensure S3 buckets are encrypted",
                    "keys": ["aws_s3_bucket.data.rule.apply_server_side_encryption_by_default.sse_algorithm"],
                },
            ]
        )
    )

    assert resources == ["aws_s3_bucket.data"]


def test_repeated_keys_on_one_resource_are_listed_once():
    _messages, resources = render._extract_detail(
        _checkov_rule(
            [
                {
                    "description": "Ensure S3 buckets are encrypted",
                    "keys": ["aws_s3_bucket.data.rule.sse_algorithm", "aws_s3_bucket.data.resource_type"],
                },
            ]
        )
    )

    assert resources == ["aws_s3_bucket.data"]


def test_a_checkov_finding_with_no_keys_still_reports_its_description():
    messages, resources = render._extract_detail(_checkov_rule([{"description": "Some check", "keys": []}]))

    assert messages == ["Some check"]
    assert resources == []


@pytest.mark.parametrize("key", ["", "single", None, 42])
def test_a_malformed_key_is_skipped_rather_than_crashing(key):
    _messages, resources = render._extract_detail(_checkov_rule([{"description": "x", "keys": [key]}]))

    assert resources == []


def test_the_tirith_shape_still_renders():
    """Teaching the renderer Checkov must not cost it the shape it already understood."""
    messages, resources = render._extract_detail(
        {
            "evaluations": {
                "fails": [
                    {"result": [{"message": "`3` is not equal to `0`", "meta": {"address": "null_resource.untagged"}}]}
                ]
            }
        }
    )

    assert messages == ["`3` is not equal to `0`"]
    assert resources == ["null_resource.untagged"]


def test_an_empty_description_does_not_hide_the_finding():
    """
    The exact shape a tirith rule with no declared description produces, taken from a QA run of the
    cost policy `DO_NOT_TOUCH / cost-control`:

        {"id": ..., "description": "", "result": [{"message": "`23.832` is not less than `20`", ...}]}

    Both keys are present. Dispatching on `"description" in entry` took the Checkov path, found an
    empty string to report, and skipped `result` -- so the policy appeared in the summary table with
    an empty <details> block. A reviewer saw that a cost rule had tripped and no reason why.
    """
    messages, resources = render._extract_detail(
        {
            "evaluations": {
                "fails": [
                    {
                        "id": "max-price-monthly-20",
                        "description": "",
                        "result": [{"passed": False, "message": "`23.832` is not less than `20`", "meta": None}],
                        "passed": False,
                    }
                ]
            }
        }
    )

    assert messages == ["`23.832` is not less than `20`"]
    # meta is None on the infracost provider -- only terraform_plan populates an address.
    assert resources == []


def test_an_entry_carrying_both_shapes_reports_both():
    """Reading both is additive, so neither shape can mask the other."""
    messages, resources = render._extract_detail(
        {
            "evaluations": {
                "fails": [
                    {
                        "description": "Ensure RDS is encrypted at rest",
                        "keys": ["aws_db_instance.db.storage_encrypted"],
                        "result": [
                            {"message": "`false` is not equal to `true`", "meta": {"address": "aws_db_instance.db"}}
                        ],
                    }
                ]
            }
        }
    )

    assert messages == ["Ensure RDS is encrypted at rest", "`false` is not equal to `true`"]
    assert resources == ["aws_db_instance.db"]


def test_an_engine_error_is_still_surfaced_verbatim():
    messages, _resources = render._extract_detail(
        {"evaluations": {"fails": [{"exec_err": "Checkov policy has no configPolicyIds"}]}}
    )

    assert messages == ["engine: Checkov policy has no configPolicyIds"]


# --- the scanned commit --------------------------------------------------------------------------
#
# The comment is edited in place across runs, so without this a reader cannot tell whether the
# verdict in front of them is about the head of the branch or about a push from an hour ago.


def test_the_scanned_commit_is_rendered_under_the_headline():
    body = render.render_markdown(_results(), "COMPLETED", "https://run", commit="9ea6388f1c2d3e4f5a6b")

    lines = body.split("\n")
    heading = next(i for i, line in enumerate(lines) if line.startswith("## "))
    assert lines[heading + 2] == "<sub>Scanned commit <code>9ea6388</code></sub>", lines[: heading + 4]


def test_no_commit_line_when_none_is_supplied():
    body = render.render_markdown(_results(), "COMPLETED", "https://run")

    assert "Scanned commit" not in body


def test_the_commit_line_survives_alongside_the_marker():
    """The marker has to stay line 1 -- it is what finds the comment again."""
    marker = "[//]: <> (tirith-comment, tag=default)"
    body = render.render_markdown(_results(), "COMPLETED", "https://run", marker=marker, commit="abc1234def")

    assert body.startswith(marker)
    assert "<code>abc1234</code>" in body


def test_a_non_sha_revision_is_not_truncated():
    """A tag or branch name is more useful whole; truncating one invents something sha-shaped."""
    body = render.render_markdown(_results(), "COMPLETED", "https://run", commit="release-2026-08")

    assert "<code>release-2026-08</code>" in body


def test_a_short_sha_is_left_alone():
    body = render.render_markdown(_results(), "COMPLETED", "https://run", commit="abc1234")

    assert "<code>abc1234</code>" in body


# --- a paused run, and results this module cannot read --------------------------------------------


def test_a_fail_is_never_downgraded_by_a_paused_run():
    """
    The regression this pins: the APPROVAL_REQUIRED branch returned before the FAIL check, so a
    paused run carrying a failing policy reported `warned` -- a neutral check, which SATISFIES a
    required status check -- while the headline on the same counts said "1 failed".
    """
    counts = {"FAIL": 1, "PASS": 2}

    assert render.verdict(counts, "APPROVAL_REQUIRED") == "failed"


def test_a_rule_with_no_result_is_not_a_pass():
    """`rule.get("result", PASS)` turned "the step wrote no verdict" into a clean bill of health."""
    counts, findings = render.summarize({"p": [{"rule_name": "r"}]})

    assert counts[render.UNKNOWN] == 1
    assert counts[render.PASS] == 0
    assert render.verdict(counts, "COMPLETED") == "errored"
    assert findings[0]["result"] == render.UNKNOWN


def test_a_result_this_module_does_not_recognise_is_not_silently_dropped():
    """
    An unrecognised value used to land in a count key `verdict` never inspects, so it vanished: the
    run reported `no-policies` and exited 0.
    """
    counts, _ = render.summarize({"p": [{"rule_name": "r", "result": "ERROR"}]})

    assert render.verdict(counts, "COMPLETED") == "errored"


def test_a_fail_still_outranks_an_unreadable_result():
    counts, _ = render.summarize({"p": [{"rule_name": "a", "result": "FAIL"}, {"rule_name": "b", "result": "?"}]})

    assert render.verdict(counts, "COMPLETED") == "failed"


# --- hostile input: the report must not be spoofable (pentest F1) --------------------------------
#
# A pull-request author controls the terraform a plan is built from, so evaluator messages, resource
# addresses, rule names and policy ids are all attacker-influenced. Before this, every one of them was
# interpolated raw or wrapped in a single backtick -- and a backtick in the value closes that span, so
# the rest rendered as markdown and HTML. A pen test used it to put a fake "all policies passed" banner
# and a link whose text said app.stackguardian.io and whose href said somewhere else into the comment a
# reviewer reads. The gate itself was never affected; the report was.
#
# These assert against markdown RENDERED by a CommonMark parser, not against the source. The payload is
# still present in the source by design -- inside a code span, where it is inert -- so a substring check
# on the source proves nothing. Getting that wrong is easy: it is the mistake made while writing these.

PAYLOAD = (
    "`x` is not equal to `y`` </details><h1>All policies passed</h1>"
    "[app.stackguardian.io](https://evil.example) | broken | cell"
)


def _render(**overrides):
    finding = {
        "rule_name": "cost-control",
        "result": "FAIL",
        "evaluations": {
            "fails": [{"result": [{"message": "ordinary message", "meta": {"address": "aws_s3_bucket.b"}}]}]
        },
    }
    policy_id = overrides.pop("policy_id", "DO_NOT_TOUCH")
    if "message" in overrides:
        finding["evaluations"]["fails"][0]["result"][0]["message"] = overrides.pop("message")
    if "address" in overrides:
        finding["evaluations"]["fails"][0]["result"][0]["meta"]["address"] = overrides.pop("address")
    finding.update(overrides)
    return render.render_markdown({policy_id: [finding]}, "COMPLETED", "https://dash.example/run/1")


def _html_of(body):
    """Render as GitHub would, so the assertions are about what a reviewer's browser receives."""
    pytest.importorskip("markdown_it", reason="needs markdown-it-py to render the assertion subject")
    from markdown_it import MarkdownIt

    return MarkdownIt("commonmark").enable("table").render(body)


@pytest.mark.parametrize("field", ["message", "address", "rule_name", "policy_id"])
def test_no_field_can_inject_markup_into_the_report(field):
    """
    Every attacker-influenced field, through the same payload. `rule_name` mattered most: it was the one
    field interpolated with no wrapping at all, straight into the `<summary>` element.
    """
    rendered = _html_of(_render(**{field: PAYLOAD}))

    assert "<h1>" not in rendered, f"{field} injected a heading"
    assert 'href="https://evil.example"' not in rendered, f"{field} injected a link"
    assert rendered.count("<details>") == rendered.count("</details>"), f"{field} broke the collapsible"


def test_the_payload_is_still_readable_after_being_neutralised():
    """
    Neutralising must not mean hiding. A reviewer has to be able to see what the policy actually
    compared, or the fix trades a spoofing bug for a blind gate.
    """
    rendered = _html_of(_render(message=PAYLOAD))

    assert "All policies passed" in rendered
    assert "&lt;h1&gt;" in rendered, "the markup should be shown as text, not dropped"


def test_a_pipe_or_newline_in_a_table_cell_keeps_the_row_intact():
    """
    A pipe splits a cell and a newline ends the row, so either one silently drops the real columns.
    GFM's remedy is a backslash escape, which is the one escape that works inside a code span.
    """
    body = _render(rule_name="a | b\nsecond line", address="x | y")

    rows = [line for line in body.splitlines() if line.startswith("|")]
    assert len(rows) == 3, f"expected header, separator and one row; got {len(rows)}"
    # Count only *unescaped* pipes -- an escaped `\|` is content, which is the whole point.
    separators = len(re.findall(r"(?<!\\)\|", rows[2]))
    assert separators == 5, f"row gained or lost a column: {rows[2]}"
    assert "second line" in rows[2], "the newline should collapse into the cell, not end the row"


def test_a_stray_backtick_cannot_open_a_span_from_inside_the_summary():
    """
    `html.escape` does not touch backticks. They cannot *close* a span in the summary because there is
    none -- but an odd one OPENS one that runs on and swallows the markdown after it, so the findings
    below the summary stop rendering as a list.
    """
    body = _render(rule_name="cost-control`")

    summary = next(line for line in body.splitlines() if "<summary>" in line)
    assert "`" not in summary, f"an unescaped backtick survived into the summary: {summary}"
    assert "&#96;" in summary, "the backtick should be shown as an entity, not dropped"


def test_the_run_url_cannot_break_out_of_the_href():
    from html.parser import HTMLParser

    class Anchors(HTMLParser):
        def __init__(self):
            super().__init__()
            self.attrs_seen = []

        def handle_starttag(self, tag, attrs):
            if tag == "a":
                self.attrs_seen.append(dict(attrs))

    body = render.render_markdown({}, "COMPLETED", 'https://dash.example/1" onmouseover="alert(1)')
    parser = Anchors()
    parser.feed(_html_of(body))

    assert parser.attrs_seen, "expected the run link to be rendered"
    for attributes in parser.attrs_seen:
        assert list(attributes) == ["href"], f"the URL introduced an attribute: {list(attributes)}"


def test_a_benign_value_renders_exactly_as_before():
    """
    The regression guard for the fence approach: with no backticks in the value the fence is a single
    backtick, so ordinary reports are byte-identical to what they were. If this breaks, every report
    changed appearance and the diff is bigger than intended.
    """
    body = _render()

    assert "| ❌ | `DO_NOT_TOUCH` | `cost-control` | `aws_s3_bucket.b` |" in body
    assert "- `ordinary message`" in body
