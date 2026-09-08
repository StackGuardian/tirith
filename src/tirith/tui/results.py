"""
Read the engine's result document into something a UI can render.

This exists because the information the pretty printer drops is the information you actually
want when a policy fails. `pretty_print_result_dict` prints a check's message and nothing else,
but each result carries a `meta` block that, for terraform_plan, is the whole resource_change:
its address, its type, the planned actions, and the before/after values. On a plan with
hundreds of resources, "FAILED: `false` is not equal to `true`" is not an answer to "which
bucket?" -- and today the only way to get the answer is to pipe --json into jq.

Nothing here mutates the result document or re-runs anything. These are read-only views over
whatever `start_policy_evaluation*` returned, so the Explorer can also open a --json file
captured from a CI run months ago.

Kept free of textual imports so it can be tested on CI's Python 3.8 leg.
"""

from typing import Any, Dict, Iterator, List, NamedTuple, Optional

from .. import plan_actions

# The tri-state a check reports. `None` means skipped, and skipped is not a pass -- the engine
# is careful about this distinction (see the --fail-on-error commentary in cli.py) and so is
# every count here.
PASSED = "passed"
FAILED = "failed"
SKIPPED = "skipped"


def status_of(passed: Optional[bool]) -> str:
    """Map a check's tri-state `passed` onto a status name."""
    if passed is None:
        return SKIPPED
    return PASSED if passed else FAILED


class ResourceRef(NamedTuple):
    """
    The resource a single result came from, when the provider recorded one.

    Only terraform_plan populates `meta` richly; the json and sg_workflow providers pass None,
    and infracost aggregates across resources so there is no single one to name. Everything
    here is therefore optional, and `is_empty` says whether there is anything to show.
    """

    address: str = ""
    resource_type: str = ""
    name: str = ""
    mode: str = ""
    provider_name: str = ""
    actions: tuple = ()

    @property
    def is_empty(self) -> bool:
        return not (self.address or self.resource_type or self.actions)

    @property
    def action_summary(self) -> str:
        """The planned action, in terraform's own vocabulary."""
        return plan_actions.action_summary(self.actions)

    @property
    def label(self) -> str:
        """The most specific name available, for a list row."""
        return self.address or self.resource_type or self.name or ""


class Result(NamedTuple):
    """One evaluated value within a check."""

    # Named `position` rather than `index` because NamedTuple inherits tuple.index().
    position: int
    passed: Optional[bool]
    message: str
    resource: ResourceRef
    # The untouched meta block, for the detail pane's raw view. May be None.
    raw_meta: Optional[Dict]

    @property
    def status(self) -> str:
        return status_of(self.passed)


class Check(NamedTuple):
    """One evaluator from the policy, with everything it produced."""

    id: str
    description: str
    passed: Optional[bool]
    results: List[Result]

    @property
    def status(self) -> str:
        return status_of(self.passed)

    @property
    def counts(self) -> Dict[str, int]:
        counts = {PASSED: 0, FAILED: 0, SKIPPED: 0}
        for result in self.results:
            counts[result.status] += 1
        return counts

    @property
    def summary(self) -> str:
        """A one-line count for the check's row, e.g. `3 passed, 1 failed`."""
        counts = self.counts
        parts = [f"{counts[status]} {status}" for status in (FAILED, PASSED, SKIPPED) if counts[status]]
        return ", ".join(parts) if parts else "no results"

    def failing_results(self) -> List[Result]:
        return [r for r in self.results if r.passed is False]


class Report(NamedTuple):
    """A whole evaluation, as the Explorer sees it."""

    checks: List[Check]
    final_result: Optional[bool]
    # True when the document had no `final_result` key at all, which the engine does when the
    # policy could not be loaded -- distinct from a final_result of None (everything skipped).
    final_result_absent: bool
    eval_expression: str
    errors: List[str]
    meta: Dict[str, Any]

    @property
    def counts(self) -> Dict[str, int]:
        counts = {PASSED: 0, FAILED: 0, SKIPPED: 0}
        for check in self.checks:
            counts[check.status] += 1
        return counts

    @property
    def verdict(self) -> str:
        """
        The policy's overall outcome.

        Mirrors the tri-state the CLI gates on under --fail-on-error, including the part that
        is easy to get wrong: a final_result of None means every check was skipped, which is
        not a pass. See the commentary in cli.py.
        """
        if self.final_result_absent:
            return "errored"
        if self.final_result is None:
            return SKIPPED
        return PASSED if self.final_result else FAILED

    @property
    def headline(self) -> str:
        counts = self.counts
        return f"{counts[PASSED]} passed · {counts[FAILED]} failed · {counts[SKIPPED]} skipped"

    def check_by_id(self, check_id: str) -> Optional[Check]:
        for check in self.checks:
            if check.id == check_id:
                return check
        return None

    def failing_checks(self) -> List[Check]:
        return [c for c in self.checks if c.passed is False]

    def iter_failing_results(self) -> Iterator["Result"]:
        for check in self.failing_checks():
            for result in check.failing_results():
                yield result


def _resource_from_meta(meta: Any) -> ResourceRef:
    """
    Pull the resource identity out of a provider's meta block.

    Shaped around terraform_plan, whose meta is the resource_change verbatim. Other providers
    pass None or something unrecognised, which yields an empty ref rather than an error --
    a UI showing "no resource detail" is correct there, not a failure.
    """
    if not isinstance(meta, dict):
        return ResourceRef()

    change = meta.get("change")
    actions = ()
    if isinstance(change, dict):
        raw_actions = change.get("actions")
        if isinstance(raw_actions, list):
            actions = tuple(raw_actions)

    return ResourceRef(
        address=meta.get("address") or "",
        resource_type=meta.get("type") or "",
        name=meta.get("name") or "",
        mode=meta.get("mode") or "",
        provider_name=meta.get("provider_name") or "",
        actions=actions,
    )


def parse_report(result_dict: Any) -> Report:
    """
    Build a Report from whatever `start_policy_evaluation` returned, or from a --json file.

    Tolerant by construction. The input may be a result document from an older tirith, a file
    the user picked by mistake, or -- in the playground -- the output of a policy that failed
    to load and therefore has `errors` and nothing else. Anything unreadable becomes an empty
    section rather than an exception, because the UI's job in that case is to show the errors.

    :param result_dict: A parsed result document.
    :return:            The report, with empty sections where the document had none.
    """
    if not isinstance(result_dict, dict):
        return Report([], None, True, "", ["Result document is not a JSON object."], {})

    checks: List[Check] = []
    for check_dict in result_dict.get("evaluators") or []:
        if not isinstance(check_dict, dict):
            continue

        results: List[Result] = []
        for position, result_dict_inner in enumerate(check_dict.get("result") or []):
            if not isinstance(result_dict_inner, dict):
                continue
            meta = result_dict_inner.get("meta")
            results.append(
                Result(
                    position=position,
                    passed=result_dict_inner.get("passed"),
                    message=str(result_dict_inner.get("message", "")),
                    resource=_resource_from_meta(meta),
                    raw_meta=meta if isinstance(meta, dict) else None,
                )
            )

        checks.append(
            Check(
                id=str(check_dict.get("id", "")),
                description=str(check_dict.get("description") or ""),
                passed=check_dict.get("passed"),
                results=results,
            )
        )

    errors = [str(e) for e in (result_dict.get("errors") or [])]
    meta = result_dict.get("meta")

    return Report(
        checks=checks,
        final_result=result_dict.get("final_result"),
        final_result_absent="final_result" not in result_dict,
        eval_expression=str(result_dict.get("eval_expression", "")),
        errors=errors,
        meta=meta if isinstance(meta, dict) else {},
    )


class AttributeChange(NamedTuple):
    """One attribute's before/after within a planned change."""

    name: str
    before: Any
    after: Any
    # terraform reports values it cannot know until apply separately from real values; showing
    # them as `null` would misrepresent a computed value as an absent one.
    after_unknown: bool = False

    @property
    def is_addition(self) -> bool:
        return self.before is None and self.after is not None

    @property
    def is_removal(self) -> bool:
        return self.before is not None and self.after is None


def attribute_changes(raw_meta: Optional[Dict]) -> List[AttributeChange]:
    """
    The changed attributes of a terraform resource_change, as a diff.

    Returns only attributes that actually differ, which is what makes this readable: a plan's
    `after` block lists every attribute of the resource, and showing all of them buries the two
    that changed. Attributes whose value is unknown until apply are included and flagged,
    since "this becomes something we cannot predict" is itself worth seeing.

    Empty for a create or a destroy, where there is no before/after pair to compare -- the
    caller should show the whole `after` (or `before`) block instead.
    """
    if not isinstance(raw_meta, dict):
        return []
    change = raw_meta.get("change")
    if not isinstance(change, dict):
        return []

    before = change.get("before")
    after = change.get("after")
    if not isinstance(before, dict) or not isinstance(after, dict):
        return []

    after_unknown = change.get("after_unknown")
    unknown_keys = set()
    if isinstance(after_unknown, dict):
        unknown_keys = {key for key, value in after_unknown.items() if value is True}

    changes: List[AttributeChange] = []
    for key in sorted(set(before) | set(after) | unknown_keys):
        old_value = before.get(key)
        new_value = after.get(key)
        is_unknown = key in unknown_keys
        if not is_unknown and old_value == new_value:
            continue
        changes.append(AttributeChange(name=key, before=old_value, after=new_value, after_unknown=is_unknown))
    return changes
