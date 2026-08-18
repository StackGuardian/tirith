"""
Turning model objects into display strings.

Split out from the widgets so it can be tested without a running terminal, and so the two
views that show a verdict show it identically.

One rule throughout: a verdict is never communicated by colour alone. Every status carries a
glyph as well, because colour is invisible to a good fraction of users, and because these
strings also end up in a browser via `textual serve` and in terminal recordings.
"""

import json
from typing import Any, List, Optional

from . import results

# Glyph and CSS class per status. Deliberately ASCII-safe apart from the check and cross,
# which render on every terminal worth supporting.
_STATUS_GLYPHS = {
    results.PASSED: "✔",
    results.FAILED: "✘",
    results.SKIPPED: "=",
    "errored": "!",
}

_STATUS_CLASSES = {
    results.PASSED: "verdict-pass",
    results.FAILED: "verdict-fail",
    results.SKIPPED: "verdict-skip",
    "errored": "verdict-error",
}


def status_glyph(status: str) -> str:
    return _STATUS_GLYPHS.get(status, "?")


def status_class(status: str) -> str:
    return _STATUS_CLASSES.get(status, "verdict-skip")


def status_markup(status: str, label: Optional[str] = None) -> str:
    """
    A status as Rich markup, glyph first.

    :param status: One of the results module's status names.
    :param label:  Text to show after the glyph. Defaults to the status name itself.
    """
    text = label if label is not None else status.upper()
    colours = {
        results.PASSED: "green",
        results.FAILED: "red",
        results.SKIPPED: "bright_black",
        "errored": "yellow",
    }
    colour = colours.get(status, "white")
    return f"[{colour}]{status_glyph(status)} {escape(text)}[/{colour}]"


def escape(text: str) -> str:
    """
    Neutralise Rich markup in text we did not write.

    Policy ids, resource addresses and provider messages all reach the screen, and any of them
    can contain a `[` -- a terraform address with an index (`aws_instance.web[0]`) does by
    definition. Without this, Rich reads that as a style tag and either swallows the text or
    raises. Not a security boundary, just correctness.
    """
    return str(text).replace("[", r"\[")


def check_label(check: results.Check) -> str:
    """A check's row in the tree: status, id, and what its results did."""
    return f"{status_markup(check.status, check.id)} [dim]{escape(check.summary)}[/dim]"


def result_label(result: results.Result) -> str:
    """
    A single result's row.

    Leads with the resource address when there is one. That ordering is the point of the
    Explorer: on a wildcard policy every message reads the same and only the address
    distinguishes them.
    """
    resource = result.resource
    if resource.label:
        suffix = f" [dim]({escape(resource.action_summary)})[/dim]" if resource.action_summary else ""
        return f"{status_markup(result.status, resource.label)}{suffix}"
    return status_markup(result.status, _truncate(result.message, 70))


def _truncate(text: str, limit: int) -> str:
    text = str(text)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def format_value(value: Any, limit: int = 400) -> str:
    """
    Render a JSON value for display.

    Strings pass through unquoted; everything else is JSON, so `null`, `true` and `{}` are
    unambiguous. The engine's own messages quote values this way, and a value shown as
    `None` when the policy must say `null` is a trap worth not laying.
    """
    if isinstance(value, str):
        return _truncate(value, limit)
    try:
        return _truncate(json.dumps(value), limit)
    except (TypeError, ValueError):
        return _truncate(repr(value), limit)


def attribute_diff_lines(result: results.Result) -> List[str]:
    """
    The changed attributes behind a result, as `name: before → after` lines.

    Empty when the provider recorded no before/after pair -- a create, a destroy, or any
    non-terraform provider. The caller shows the resource's current values instead.
    """
    lines = []
    for change in results.attribute_changes(result.raw_meta):
        if change.after_unknown:
            after = "[italic]known after apply[/italic]"
        else:
            after = escape(format_value(change.after, 120))
        before = escape(format_value(change.before, 120))
        lines.append(f"[bold]{escape(change.name)}[/bold]: {before} → {after}")
    return lines


def resource_lines(result: results.Result) -> List[str]:
    """The resource identity block for the detail pane."""
    resource = result.resource
    if resource.is_empty:
        return []

    lines = []
    if resource.address:
        lines.append(f"[bold]{escape(resource.address)}[/bold]")
    if resource.action_summary:
        lines.append(f"Action: {escape(resource.action_summary)}")
    if resource.resource_type:
        lines.append(f"Type: {escape(resource.resource_type)}")
    if resource.mode:
        lines.append(f"Mode: {escape(resource.mode)}")
    if resource.provider_name:
        lines.append(f"Provider: {escape(resource.provider_name)}")
    return lines


def report_headline(report: results.Report) -> str:
    """The one-line verdict shown above the results."""
    verdict_names = {
        results.PASSED: "Policy passed",
        results.FAILED: "Policy failed",
        results.SKIPPED: "Policy skipped every check",
        "errored": "Policy did not produce a verdict",
    }
    verdict = report.verdict
    return f"{status_markup(verdict, verdict_names.get(verdict, verdict))}  [dim]{escape(report.headline)}[/dim]"


def finding_markup(finding) -> str:
    """A validator finding, coloured by severity."""
    colour = "red" if finding.severity == "error" else "yellow"
    glyph = "✘" if finding.severity == "error" else "▲"
    return f"[{colour}]{glyph} {escape(finding.where)}[/{colour}] {escape(finding.message)}"
