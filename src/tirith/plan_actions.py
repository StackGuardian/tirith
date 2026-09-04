"""
Terraform plan actions, in vocabulary a human reads.

Shared because two very different surfaces need the same answer: the TUI's result list and the
pull-request comment. Keeping one implementation is what stops them disagreeing about whether
`["delete", "create"]` is a replacement or two separate operations.
"""

import json

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


# Rendered in place of a value we must not or cannot print. Both are terraform's own wording, so a
# reader who knows plan output needs no translation.
SENSITIVE = "(sensitive value)"
UNKNOWN = "(known after apply)"


def _contains_true(node):
    """
    Whether a sensitivity or unknown-ness tree marks anything at all.

    These trees mirror the *shape* of the value rather than being booleans: terraform reports
    `{"triggers_replace": [false]}`, where the list is structure and the `false` is the answer. A
    truthy test on the node therefore says "sensitive" for a list that says the opposite -- which is
    how a first attempt printed "(sensitive value)" over a value that was never secret.

    Any `True` anywhere means the whole value is treated as marked. That is deliberately
    conservative: for sensitivity it over-hides rather than leaks, and for unknown-ness it prefers
    "we cannot show this" to printing half a value as if it were whole.
    """
    if node is True:
        return True
    if isinstance(node, dict):
        return any(_contains_true(v) for v in node.values())
    if isinstance(node, list):
        return any(_contains_true(v) for v in node)
    return False


def attribute_changes(change, limit=8):
    """
    Per-attribute changes for one resource, as (marker, key, before, after, forces_replacement).

    `before` and `after` are already rendered to strings here, because whether a value may be shown
    at all is plan semantics -- sensitivity and unknown-ness live in the document -- while *how* to
    make a string safe for the surface it lands on belongs to the renderer.

    What each action shows, and why it differs:

      create   every attribute with a known value. The unknown ones are what terraform fills in, and
               a wall of "(known after apply)" says nothing a reader can act on, so they are counted.
      update   only what changed. That is the whole question being asked.
      replace  the same, plus which attribute forced it -- the most useful line in a plan review.
      delete   nothing. The resource is going away; its former values neither inform the decision nor
               belong in a public comment.
    """
    actions = tuple(a for a in ((change or {}).get("actions") or []) if a)
    if not actions or actions == ("no-op",) or actions == ("delete",):
        return [], 0, 0

    before = (change.get("before") or {}) if isinstance(change.get("before"), dict) else {}
    after = (change.get("after") or {}) if isinstance(change.get("after"), dict) else {}
    unknown = change.get("after_unknown") or {}
    after_sensitive = change.get("after_sensitive")
    after_sensitive = after_sensitive if isinstance(after_sensitive, dict) else {}
    before_sensitive = change.get("before_sensitive")
    before_sensitive = before_sensitive if isinstance(before_sensitive, dict) else {}
    forces = {path[0] for path in (change.get("replace_paths") or []) if path}

    creating = actions == ("create",)
    rows = []
    hidden_unknown = 0

    for key in sorted(set(before) | set(after) | (set(unknown) if isinstance(unknown, dict) else set())):
        node = unknown.get(key) if isinstance(unknown, dict) else None
        is_unknown = _contains_true(node)
        old, new = before.get(key), after.get(key)

        if not is_unknown and old == new:
            continue

        if creating:
            if is_unknown:
                # Counted rather than printed: on a create these are every computed attribute, and
                # naming them crowds out the values the author actually chose.
                hidden_unknown += 1
                continue
            rows.append(("+", key, None, _render_value(new, after_sensitive.get(key)), key in forces))
            continue

        rows.append(
            (
                "~",
                key,
                _render_value(old, before_sensitive.get(key)),
                UNKNOWN if is_unknown else _render_value(new, after_sensitive.get(key)),
                key in forces,
            )
        )

    dropped = max(0, len(rows) - limit)
    return rows[:limit], dropped, hidden_unknown


def _render_value(value, sensitivity_node):
    if _contains_true(sensitivity_node):
        return SENSITIVE
    if value is None:
        return "null"
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    # Nested structures are compacted rather than rendered as a tree. A full nested diff is a much
    # larger feature, and a compact form still answers "did this change and roughly to what".
    return json.dumps(value, separators=(",", ":"), sort_keys=True)
