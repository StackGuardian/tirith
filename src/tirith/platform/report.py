"""
Turn PolicyEvalResults into a PR comment body, a check-run summary, and a verdict.

Pure functions over the results document so the layout and the truncation arithmetic can be tested
without touching a network.
"""

FAIL = "FAIL"
WARN = "WARN"
PASS = "PASS"
APPROVAL_REQUIRED = "APPROVAL_REQUIRED"

# Anything the step reports that is not one of the four above. It is counted separately and treated
# as unresolved rather than folded into any of them: a result this module does not understand is not
# evidence of a pass, and bucketing it under a key `verdict` never inspects made it one.
UNKNOWN = "UNKNOWN"

# GitHub rejects an issue-comment body over 65536 characters and a check-run output.summary over
# 65535. Budget well under both: the count that matters is characters after rendering, and a
# 422 at the end of a run is a bad way to find out.
COMMENT_LIMIT = 60000

_ICONS = {FAIL: "❌", WARN: "⚠️", APPROVAL_REQUIRED: "⏳", PASS: "✅"}


def summarize(policy_results):
    """
    Collapse the results into counts plus a flat finding list.

    A rule marked `skip` carries no verdict, so it is counted separately rather than being
    folded into passes -- reporting a skipped control as passing is the kind of quiet
    inaccuracy this whole design exists to avoid.
    """
    counts = {FAIL: 0, WARN: 0, APPROVAL_REQUIRED: 0, PASS: 0, "SKIPPED": 0, UNKNOWN: 0}
    findings = []

    for policy_id, rules in sorted((policy_results or {}).items()):
        for rule in rules or []:
            if rule.get("skip"):
                counts["SKIPPED"] += 1
                findings.append(
                    {
                        "policy_id": policy_id,
                        "rule_name": rule.get("rule_name", ""),
                        "result": "SKIPPED",
                        "messages": [],
                        "resources": [],
                    }
                )
                continue

            # No default of PASS: a rule the step wrote without a `result`, or with one this module
            # does not know, is unresolved. Defaulting to PASS turned "we cannot tell" into a clean
            # bill of health, and an unrecognised value landed in a count key `verdict` never reads,
            # so it disappeared entirely.
            result = rule.get("result")
            if result not in (FAIL, WARN, APPROVAL_REQUIRED, PASS):
                result = UNKNOWN
            counts[result] = counts.get(result, 0) + 1
            messages, resources = _extract_detail(rule)
            findings.append(
                {
                    "policy_id": policy_id,
                    "rule_name": rule.get("rule_name", ""),
                    "result": result,
                    "messages": messages,
                    "resources": resources,
                }
            )

    return counts, findings


def _extract_detail(rule):
    """Pull human-readable messages and resource addresses out of a rule's evaluations."""
    messages = []
    resources = []

    for entry in (rule.get("evaluations") or {}).get("fails") or []:
        if "exec_err" in entry:
            # An engine/config problem rather than a policy violation -- surfaced verbatim so a
            # malformed policy is not mistaken for a real finding.
            messages.append(f"engine: {entry['exec_err']}")
            continue

        # Checkov findings are shaped differently from tirith's: {"description", "keys"} rather
        # than a list under "result". Reading only the tirith shape rendered a Checkov policy as an
        # empty <details> block -- a dozen real findings, silently blank, in the one place a
        # reviewer looks.
        if "description" in entry:
            description = entry.get("description")
            if description:
                messages.append(description)
            for key in entry.get("keys") or []:
                # `aws_instance.app.root_block_device` -> `aws_instance.app`. The suffix is the
                # attribute the check looked at; the address is what a reviewer navigates by.
                address = _resource_address(key)
                if address and address not in resources:
                    resources.append(address)
            continue

        for evaluation in entry.get("result") or []:
            message = evaluation.get("message")
            if message:
                messages.append(message)
            # Only the terraform_plan provider populates meta; others set it to None.
            meta = evaluation.get("meta") or {}
            address = meta.get("address") if isinstance(meta, dict) else None
            if address and address not in resources:
                resources.append(address)

    return messages, resources


def _resource_address(key):
    """
    Reduce a Checkov evaluated key to the resource address it belongs to.

    Checkov reports `<type>.<name>.<attribute path>`, and the attribute path can be arbitrarily
    deep (`aws_s3_bucket.data.rule.apply_server_side_encryption_by_default.sse_algorithm`). The
    first two segments are the address; everything after is what the check inspected.
    """
    if not isinstance(key, str):
        return None
    parts = key.split(".")
    if len(parts) < 2:
        return None
    return ".".join(parts[:2])


def verdict(counts, run_status):
    """
    Reduce counts and run status to one word.

    failed | warned | passed | no-policies | errored

    `errored` covers a run that never produced a verdict -- an ERRORED/CANCELLED run, or results
    that came back empty. It is deliberately distinct from `failed` so the caller can tell "a
    policy said no" from "we do not know", and never conflate either with a pass.

    A policy carrying `onFail: APPROVAL_REQUIRED` warns; it does not gate. That is a deliberate
    interim position, because for these runs there is nothing to approve. The step exits 0 (it never
    uses exit 11), so the run reaches COMPLETED, and the run controller engages an approval only on
    exit 11 and skips it on the last step anyway -- and a policy-only run has exactly one step. So
    the approval intent arrives as a count on an already-finished run, with no approval to act on.
    Blocking on it produced a red check with nothing to click.

    The count, the icon and the "N need approval" phrase in the headline all survive, so the policy
    author's intent is still visible in the comment. Gating on it properly needs a run that stays
    open, an approve action on it, and this client re-polling afterwards -- none of which exist yet.

    Run status APPROVAL_REQUIRED means the platform itself paused the run. It is ranked by the same
    ladder and then floored, rather than short-circuited: an early return there let a paused run
    carrying a FAIL report `warned`, which is the one direction that must never happen. And because
    a paused run did not finish, it can never rank better than `warned` either -- the policies that
    would have run after the pause did not, so "everything passed" is not something we know.

    A rule whose result this module does not recognise counts as UNKNOWN and lands in `errored`.
    "We cannot tell" is not a pass.
    """
    if run_status not in ("COMPLETED", "APPROVAL_REQUIRED"):
        return "errored"

    paused = run_status == "APPROVAL_REQUIRED"

    if counts.get(FAIL):
        return "failed"
    # An unreadable result outranks a warning: part of the evaluation is unaccounted for.
    if counts.get(UNKNOWN):
        return "errored"
    if counts.get(APPROVAL_REQUIRED) or counts.get(WARN):
        return "warned"
    if counts.get(PASS) or counts.get("SKIPPED"):
        return "warned" if paused else "passed"
    # No policy results at all. On a COMPLETED run that means nothing was in scope -- worth saying,
    # rather than implying a clean bill of health. On a paused run it means the evaluation never got
    # far enough to produce any, which is not "nothing in scope" but "we do not know".
    return "errored" if paused else "no-policies"


def headline(counts, verdict_value):
    if verdict_value == "errored":
        return "Tirith could not evaluate policies"
    if verdict_value == "no-policies":
        return "Tirith — no policies in scope for this workflow"

    parts = []
    for key, label in ((FAIL, "failed"), (APPROVAL_REQUIRED, "need approval"), (WARN, "warned")):
        if counts.get(key):
            parts.append(f"{counts[key]} {label}")
    if counts.get(PASS):
        parts.append(f"{counts[PASS]} passed")
    if counts.get("SKIPPED"):
        parts.append(f"{counts['SKIPPED']} skipped")
    return "Tirith — " + (", ".join(parts) if parts else "nothing evaluated")


def _short_commit(commit):
    """
    Seven characters, the length git itself abbreviates to.

    Anything that is not a hex sha is passed through untouched -- a tag or a branch name is more
    useful whole, and truncating one would produce something that looks like a sha and is not.
    """
    text = str(commit).strip()
    if len(text) > 7 and all(c in "0123456789abcdefABCDEF" for c in text):
        return text[:7]
    return text


def render_cost(breakdown):
    """
    One line of cost, for the pull-request comment.

    Rendered even when the estimate is zero or failed -- silence would be indistinguishable from
    "this change costs nothing", and those are very different things to tell a reviewer.
    Returns [] only when no estimate was attempted at all.
    """
    if not isinstance(breakdown, dict) or not breakdown:
        return []

    if breakdown.get("error"):
        return ["", "<sub>💵 Cost estimate unavailable for this plan.</sub>"]

    currency = breakdown.get("currency") or "USD"
    monthly = breakdown.get("totalMonthlyCost")
    diff = breakdown.get("diffTotalMonthlyCost")

    if monthly is None:
        return []

    try:
        monthly_text = f"{float(monthly):,.2f}"
    except (TypeError, ValueError):
        monthly_text = str(monthly)

    line = f"💵 Estimated monthly cost: **{monthly_text} {currency}**"

    # Infracost fills the diff from the plan's prior state, so it is the number a reviewer of a
    # change actually wants. Only shown when it is non-zero and distinguishable from the total.
    try:
        delta = float(diff)
    except (TypeError, ValueError):
        delta = None
    if delta:
        line += f" ({'+' if delta > 0 else '−'}{abs(delta):,.2f} from this change)"

    return ["", f"<sub>{line}</sub>"]


def render_markdown(
    policy_results, run_status, run_url, marker=None, limit=COMMENT_LIMIT, cost_breakdown=None, commit=None
):
    """
    Render the results as markdown, truncating detail before the summary table.

    `marker` is an opaque first line the caller can use to find this document again -- GitHub's
    sticky-comment marker, for instance. Kept as a parameter rather than built here so this module
    stays VCS-agnostic.

    `commit` is the revision these findings describe. It matters because the comment is *edited in
    place* across runs: without it a reader has no way to tell whether the verdict they are looking
    at is about the head of the branch or about a push from an hour ago. Rendered here rather than
    appended by the caller so the check-run summary and the job summary carry it too.
    """
    counts, findings = summarize(policy_results)
    verdict_value = verdict(counts, run_status)

    header = ([marker, ""] if marker else []) + [
        f"## 🛡️ {headline(counts, verdict_value)}",
        "",
    ]
    if commit:
        header += [f"<sub>Scanned commit <code>{_short_commit(commit)}</code></sub>", ""]

    if verdict_value == "errored":
        header += [
            f"The workflow run finished as `{run_status}` without producing policy results.",
            "This is reported as a failure rather than a pass: no verdict is not the same as a clean one.",
            "",
        ]

    table = _render_table(findings)
    # Ahead of the footer so the cost sits directly under the findings, and outside the truncation
    # path below -- a long findings list must not push the cost line out of the comment.
    cost = render_cost(cost_breakdown)
    footer = cost + _render_footer(counts, run_url)

    detail_sections = [_render_detail(f) for f in findings if f["result"] in (FAIL, APPROVAL_REQUIRED, WARN)]

    body = "\n".join(header + table + detail_sections + footer)
    if len(body) <= limit:
        return body

    # Drop detail sections from the end until it fits, keeping the summary table intact -- the
    # table is the part a reviewer scans first.
    kept = list(detail_sections)
    while kept and len(body) > limit:
        kept.pop()
        omitted = len(detail_sections) - len(kept)
        note = [f"", f"_… and {omitted} more finding(s). See the full run in StackGuardian._", ""]
        body = "\n".join(header + table + kept + note + footer)

    if len(body) > limit:
        # Even the table is too large; truncate hard rather than risk a 422.
        body = body[: limit - 200] + "\n\n_… truncated. See the full run in StackGuardian._\n"

    return body


def _render_table(findings):
    if not findings:
        return []
    rows = [
        "| | Policy | Rule | Resource |",
        "|---|---|---|---|",
    ]
    for finding in findings:
        icon = _ICONS.get(finding["result"], "⚪")
        resources = ", ".join(f"`{r}`" for r in finding["resources"][:3]) or "—"
        if len(finding["resources"]) > 3:
            resources += f" _+{len(finding['resources']) - 3}_"
        rows.append(f"| {icon} | `{finding['policy_id']}` | {finding['rule_name']} | {resources} |")
    rows.append("")
    return rows


def _render_detail(finding):
    icon = _ICONS.get(finding["result"], "⚪")
    lines = [
        "<details>",
        f"<summary><strong>{icon} {finding['policy_id']} › {finding['rule_name']}</strong></summary>",
        "",
    ]
    for message in finding["messages"][:20]:
        lines.append(f"- {message}")
    if len(finding["messages"]) > 20:
        lines.append(f"- _… and {len(finding['messages']) - 20} more_")
    if finding["resources"]:
        lines += ["", "Resources:"] + [f"- `{r}`" for r in finding["resources"][:20]]
    lines += ["", "</details>", ""]
    return "\n".join(lines)


def _render_footer(counts, run_url):
    bits = []
    if counts.get(PASS):
        bits.append(f"✅ {counts[PASS]} passed")
    if counts.get("SKIPPED"):
        bits.append(f"⚪ {counts['SKIPPED']} skipped")
    if run_url:
        bits.append(f'<a href="{run_url}">View run in StackGuardian</a>')
    return ["", f"<sub>{' · '.join(bits)}</sub>"] if bits else []


def strip_marker(body):
    """Drop the marker line, for a rendering target that has no use for it."""
    return "\n".join(line for line in body.split("\n") if not line.startswith("[//]: <>"))
