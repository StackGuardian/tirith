"""
`tirith lint` -- check policy files for the mistakes that otherwise reach CI looking like real
infrastructure violations.

Shape, not meaning. The checks come from the same validator the interactive interface runs on
every keystroke (tui/validate.py, importable without the UI toolkit by design): an invented
condition type, a `provider_args` key another provider reads, an evaluator the expression never
names, `error_tolerance` outside `condition`. None of that needs a plan document, which is what
makes it fit in a pre-commit hook. Whether a well-formed policy matches anything is a question
only evaluation answers; see the README.

Exit codes follow the rest of Tirith: `3` when a policy has an error-level finding (the linter
saying no about a policy is a verdict, not a tool failure), `1` when a path does not exist or
nothing was found to lint, `0` when every policy is clean.
"""

import argparse
import json
import sys
from typing import List

from .policyfiles import collect
from .status import ExitStatus
from .tui import validate

PROG = "tirith lint"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Check Tirith policy files for mistakes that would otherwise gate nothing or fail as a false violation.",
        epilog=(
            "With no path, lints .tirith/policies if it exists, otherwise the current directory.\n"
            "Directories are searched for *.json files; JSON that is not a policy is skipped.\n"
            "\n"
            "Exit codes:  0 every policy is clean   3 a policy has errors   1 a path is missing or nothing was found\n"
            "\n"
            "Lint checks the shape. Only evaluating against a document that should fail checks the meaning:\n"
            "    tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("paths", metavar="PATH", nargs="*", help="Policy files or directories.")
    parser.add_argument("--json", action="store_true", help="Print findings as a JSON document instead of text.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors for the exit code.")
    parser.add_argument("--quiet", action="store_true", help="Print findings only, no summary and no skipped files.")
    return parser


def lint_paths(paths: List[str], strict: bool = False) -> dict:
    """
    Lint the given paths and return a report document.

    Separated from output so the same report feeds the text and JSON renderers, and so callers in
    other programs (an editor integration, the interface) can use it without parsing text.
    """
    policies, skipped, ignored, missing = collect(paths)

    files = []
    errors = warnings = 0
    for policy_file in policies:
        if policy_file.error is not None:
            findings = [validate.Finding("error", "<file>", policy_file.error)]
        else:
            findings = validate.check_policy(policy_file.document)
        file_errors, file_warnings = validate.summarize(findings)
        errors += file_errors
        warnings += file_warnings
        files.append(
            {
                "path": policy_file.path,
                "findings": [{"severity": f.severity, "where": f.where, "message": f.message} for f in findings],
            }
        )

    if missing:
        status = ExitStatus.ERROR
    elif not files:
        status = ExitStatus.ERROR
    elif errors or (strict and warnings):
        status = ExitStatus.ERROR_POLICY_FAILED
    else:
        status = ExitStatus.SUCCESS

    return {
        "files": files,
        "skipped": skipped,
        "missing": missing,
        "summary": {"policies": len(files), "errors": errors, "warnings": warnings, "ignored": ignored},
        "exit_status": int(status),
    }


def _print_text(report: dict, quiet: bool) -> None:
    for entry in report["files"]:
        for finding in entry["findings"]:
            print(f"{entry['path']}:{finding['where']}: {finding['severity']}: {finding['message']}")
    for path in report["missing"]:
        print(f"{path}: error: no such file or directory", file=sys.stderr)

    if quiet:
        return
    for path in report["skipped"]:
        print(f"{path}: skipped, not a Tirith policy", file=sys.stderr)
    summary = report["summary"]
    if summary["policies"] == 0 and not report["missing"]:
        print(
            "No policies found. A policy is a JSON object with meta, evaluators and eval_expression.", file=sys.stderr
        )
        return
    noun = "policy" if summary["policies"] == 1 else "policies"
    line = f"{summary['policies']} {noun}, {summary['errors']} errors, {summary['warnings']} warnings"
    if summary["ignored"]:
        line += f" ({summary['ignored']} JSON files that are not policies ignored)"
    print(line)


def main(argv: List[str]) -> ExitStatus:
    parser = build_parser()
    # argv arrives including the `lint` token that dispatched us.
    opts = parser.parse_args(argv[1:] if argv and argv[0] == "lint" else argv)

    report = lint_paths(opts.paths, strict=opts.strict)
    if opts.json:
        print(json.dumps(report, indent=2))
    else:
        _print_text(report, opts.quiet)
    return ExitStatus(report["exit_status"])
