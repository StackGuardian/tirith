"""
Turn PolicyEvalResults into a PR comment body, a check-run summary, and a verdict.

Pure functions over the results document so the layout and the truncation arithmetic can be tested
without touching a network.
"""

FAIL = "FAIL"
WARN = "WARN"
PASS = "PASS"
APPROVAL_REQUIRED = "APPROVAL_REQUIRED"

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
    counts = {FAIL: 0, WARN: 0, APPROVAL_REQUIRED: 0, PASS: 0, "SKIPPED": 0}
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

            result = rule.get("result", PASS)
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


def verdict(counts, run_status):
    """
    Reduce counts and run status to one word.

    failed | warned | passed | no-policies | approval-required | errored

    `errored` covers a run that never produced a verdict -- an ERRORED/CANCELLED run, or results
    that came back empty. It is deliberately distinct from `failed` so the caller can tell "a
    policy said no" from "we do not know", and never conflate either with a pass.

    `approval-required` is a resting state, not a failure: the evaluation finished and a human now
    has to act. Reporting it as `errored` would blame the tool for a working evaluation.

    It is reached two ways, and both matter. The run status is APPROVAL_REQUIRED when the platform
    itself gated the run. A *rule* result of APPROVAL_REQUIRED means a policy author wrote
    `onFail: APPROVAL_REQUIRED`, which the policy-only step records without pausing the run -- so
    the run comes back COMPLETED and only the counts carry the intent.

    Folding that into `warned` was wrong: `warned` maps to a `neutral` check, which SATISFIES a
    required status check, so a policy demanding human sign-off silently did not block. Ranking it
    above `warned` keeps the author's intent without implementing the approval workflow, which is
    out of scope here.
    """
    if run_status == "APPROVAL_REQUIRED":
        return "approval-required"
    if run_status not in ("COMPLETED",):
        return "errored"
    if counts.get(FAIL):
        return "failed"
    if counts.get(APPROVAL_REQUIRED):
        return "approval-required"
    if counts.get(WARN):
        return "warned"
    if counts.get(PASS) or counts.get("SKIPPED"):
        return "passed"
    # A COMPLETED run with no policy results at all: nothing was in scope. Report it rather than
    # implying a clean bill of health.
    return "no-policies"


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


def render_markdown(policy_results, run_status, run_url, marker=None, limit=COMMENT_LIMIT):
    """
    Render the results as markdown, truncating detail before the summary table.

    `marker` is an opaque first line the caller can use to find this document again -- GitHub's
    sticky-comment marker, for instance. Kept as a parameter rather than built here so this module
    stays VCS-agnostic.
    """
    counts, findings = summarize(policy_results)
    verdict_value = verdict(counts, run_status)

    header = ([marker, ""] if marker else []) + [
        f"## 🛡️ {headline(counts, verdict_value)}",
        "",
    ]

    if verdict_value == "errored":
        header += [
            f"The workflow run finished as `{run_status}` without producing policy results.",
            "This is reported as a failure rather than a pass: no verdict is not the same as a clean one.",
            "",
        ]

    table = _render_table(findings)
    footer = _render_footer(counts, run_url)

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
