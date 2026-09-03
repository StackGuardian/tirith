"""
Terraform plan actions, in vocabulary a human reads.

Shared because two very different surfaces need the same answer: the TUI's result list and the
pull-request comment. Keeping one implementation is what stops them disagreeing about whether
`["delete", "create"]` is a replacement or two separate operations.
"""

# What terraform calls the operation, keyed by the exact action tuple it reports.
#
# The replacement pair is ordered, and which way round it is changes the risk rather than the
# wording: delete-then-create has downtime, create-then-delete does not. Reporting both as
# "replace" would hide the difference a reviewer most needs to see.
_ACTION_NAMES = {
    ("no-op",): "no change",
    ("create",): "create",
    ("delete",): "destroy",
    ("update",): "update in place",
    ("read",): "read",
    ("delete", "create"): "replace (destroy first)",
    ("create", "delete"): "replace (create first)",
}

# Which markers a ```diff fence understands. GitHub highlights `+`, `-` and `!` and nothing else --
# terraform's own `~` for an update renders as plain text, which defeats the point of the fence. So
# update and replace share `!` and the words carry the precision.
_CREATE = "+"
_DESTROY = "-"
_CHANGE = "!"

_ACTION_MARKERS = {
    ("create",): _CREATE,
    ("delete",): _DESTROY,
    ("update",): _CHANGE,
    ("delete", "create"): _CHANGE,
    ("create", "delete"): _CHANGE,
}


def action_summary(actions):
    """
    The planned action, in terraform's own vocabulary.

    An unrecognised combination is joined rather than dropped: a tuple this module has not seen is
    still worth showing verbatim, and inventing a friendly name for it would be a guess.
    """
    actions = tuple(a for a in actions or () if a)
    if not actions:
        return ""
    return _ACTION_NAMES.get(actions) or ", ".join(actions)


def action_marker(actions):
    """The diff marker for an action tuple, or "" for no-op and anything unrecognised."""
    actions = tuple(a for a in actions or () if a)
    return _ACTION_MARKERS.get(actions, "")


def is_no_op(actions):
    return tuple(a for a in actions or () if a) == ("no-op",)


def plan_counts(resource_changes):
    """
    Count a plan the way its summary line reports it.

    Replacements are counted on their own rather than folded into add + destroy. Terraform reports
    them inside those two, so this deliberately differs: "2 to replace" is the number that should
    make a reviewer look twice, and it disappears when it is spread across the other columns.
    """
    counts = {"add": 0, "change": 0, "destroy": 0, "replace": 0, "no_op": 0}
    for change in resource_changes or []:
        actions = tuple(a for a in ((change.get("change") or {}).get("actions") or []) if a)
        if actions in (("delete", "create"), ("create", "delete")):
            counts["replace"] += 1
        elif actions == ("create",):
            counts["add"] += 1
        elif actions == ("update",):
            counts["change"] += 1
        elif actions == ("delete",):
            counts["destroy"] += 1
        elif actions == ("no-op",):
            counts["no_op"] += 1
    return counts


def summary_line(counts):
    """
    The one line a reviewer looks for.

    `replace` is only mentioned when there is one, so the common case reads exactly like terraform's
    own summary and the unusual case is conspicuous.
    """
    parts = [
        f"{counts.get('add', 0)} to add",
        f"{counts.get('change', 0)} to change",
        f"{counts.get('destroy', 0)} to destroy",
    ]
    if counts.get("replace"):
        parts.append(f"{counts['replace']} to replace")
    return "Plan: " + ", ".join(parts) + "."
