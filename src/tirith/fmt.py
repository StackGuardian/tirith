"""
`tirith fmt` -- rewrite policy files into one canonical layout.

The layout is fixed so that two people writing the same policy produce the same bytes, and so
that a diff shows a change of meaning rather than a change of key order. It reorders keys and
normalises whitespace; it never changes a value, adds a key, or reorders a list, and the result
parses back to an equal document. `fmt --check` reports without writing, which is the pre-commit
shape; `--diff` shows what would change.
"""

import argparse
import difflib
import json
import sys
from typing import Any, Dict, List, Sequence

from .policyfiles import collect
from .status import ExitStatus

PROG = "tirith fmt"

# Key orders. Keys a document has that are not listed keep their original relative order after
# the listed ones, so an unknown key is preserved rather than dropped or sorted into surprise.
TOP_ORDER = ("$schema", "meta", "evaluators", "eval_expression")
META_ORDER = (
    "version",
    "required_provider",
    "id",
    "name",
    "description",
    "severity",
    "enforcement",
    "tags",
    "remediation",
)
EVALUATOR_ORDER = ("id", "description", "provider_args", "condition")
PROVIDER_ARGS_ORDER = ("operation_type",)
CONDITION_ORDER = ("type", "value", "error_tolerance")


def _ordered(mapping: Dict[str, Any], order: Sequence[str]) -> Dict[str, Any]:
    result = {}
    for key in order:
        if key in mapping:
            result[key] = mapping[key]
    for key in mapping:
        if key not in result:
            result[key] = mapping[key]
    return result


def canonical(document: Any) -> Any:
    """Return the document with keys in canonical order. Values and list orders are untouched."""
    if not isinstance(document, dict):
        return document
    out = _ordered(document, TOP_ORDER)
    if isinstance(out.get("meta"), dict):
        out["meta"] = _ordered(out["meta"], META_ORDER)
    if isinstance(out.get("evaluators"), list):
        evaluators = []
        for evaluator in out["evaluators"]:
            if isinstance(evaluator, dict):
                evaluator = _ordered(evaluator, EVALUATOR_ORDER)
                if isinstance(evaluator.get("provider_args"), dict):
                    evaluator["provider_args"] = _ordered(evaluator["provider_args"], PROVIDER_ARGS_ORDER)
                if isinstance(evaluator.get("condition"), dict):
                    evaluator["condition"] = _ordered(evaluator["condition"], CONDITION_ORDER)
            evaluators.append(evaluator)
        out["evaluators"] = evaluators
    return out


INDENT = "  "
# A list of scalars shorter than this stays on one line: `["public-read", "public-read-write"]`
# reads as one value, which is what it is. `json.dumps(indent=2)` would put each item on its
# own line, and every hand-written policy in this repository keeps them inline.
INLINE_LIST_WIDTH = 80


def _scalar(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _render(value: Any, depth: int) -> str:
    pad = INDENT * depth
    inner = INDENT * (depth + 1)
    if isinstance(value, dict):
        if not value:
            return "{}"
        items = [f"{inner}{_scalar(str(key))}: {_render(item, depth + 1)}" for key, item in value.items()]
        return "{\n" + ",\n".join(items) + "\n" + pad + "}"
    if isinstance(value, list):
        if not value:
            return "[]"
        if all(not isinstance(item, (dict, list)) for item in value):
            inline = "[" + ", ".join(_scalar(item) for item in value) + "]"
            if len(pad) + len(inline) <= INLINE_LIST_WIDTH:
                return inline
        items = [f"{inner}{_render(item, depth + 1)}" for item in value]
        return "[\n" + ",\n".join(items) + "\n" + pad + "]"
    return _scalar(value)


def format_policy(document: Any) -> str:
    """
    Canonical text for a parsed policy.

    Two-space indent, one key per line, short scalar lists inline, non-ASCII kept as written,
    one trailing newline. Parses back to a document equal to the input.
    """
    return _render(canonical(document), 0) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Rewrite Tirith policy files into the canonical layout.",
        epilog=(
            "With no path, formats .tirith/policies if it exists, otherwise the current directory.\n"
            "Keys are ordered meta, evaluators, eval_expression; inside a check id, description,\n"
            "provider_args, condition. Values and list order are never changed.\n"
            "\n"
            "Exit codes:  0 nothing to change (or written)   3 --check found files that would change\n"
            "             1 a path is missing, a file is not valid JSON, or nothing was found"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("paths", metavar="PATH", nargs="*", help="Policy files or directories.")
    parser.add_argument("--check", action="store_true", help="Do not write. Exit 3 if any file would change.")
    parser.add_argument("--diff", action="store_true", help="Print a unified diff of the changes. Implies --check.")
    return parser


def main(argv: List[str]) -> ExitStatus:
    parser = build_parser()
    opts = parser.parse_args(argv[1:] if argv and argv[0] == "fmt" else argv)
    check = opts.check or opts.diff

    policies, skipped, _ignored, missing = collect(opts.paths)
    for path in missing:
        print(f"{path}: error: no such file or directory", file=sys.stderr)
    for path in skipped:
        print(f"{path}: skipped, not a Tirith policy", file=sys.stderr)

    unreadable = [p for p in policies if p.error is not None]
    for policy_file in unreadable:
        print(f"{policy_file.path}: error: {policy_file.error}", file=sys.stderr)

    changed = []
    for policy_file in policies:
        if policy_file.error is not None:
            continue
        formatted = format_policy(policy_file.document)
        if formatted == policy_file.text:
            continue
        changed.append(policy_file.path)
        if opts.diff:
            sys.stdout.writelines(
                difflib.unified_diff(
                    policy_file.text.splitlines(keepends=True),
                    formatted.splitlines(keepends=True),
                    fromfile=policy_file.path,
                    tofile=policy_file.path,
                )
            )
        elif check:
            print(policy_file.path)
        else:
            with open(policy_file.path, "w", encoding="utf-8") as f:
                f.write(formatted)
            print(policy_file.path)

    if missing or unreadable:
        return ExitStatus.ERROR
    if not policies:
        print(
            "No policies found. A policy is a JSON object with meta, evaluators and eval_expression.", file=sys.stderr
        )
        return ExitStatus.ERROR
    if check and changed:
        return ExitStatus.ERROR_POLICY_FAILED
    return ExitStatus.SUCCESS
