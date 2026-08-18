"""
The aggregate path behind `tirith -policy-path ...`.

The flat command has always evaluated exactly one policy file and printed the engine's own document.
That is the right shape for a person at a terminal and the wrong one for a CI job, which needs many
policies from a directory, the input masked before its values reach a pull-request comment, and one
verdict written out for something else to publish.

This module is that second shape. It is reached only when the caller asks for it -- a policy path that
is not a single file, or any of the reporting flags -- so the original path, and the frozen `--json`
output it prints, are untouched.

It writes the same two files `tirith platform check` writes, in the same shapes, so a front end can
drive either with one argv and one parser.
"""

import os
import tempfile

from ..platform import report
from ..platform.check import log, write_output_json, write_output_markdown
from .evaluate import LocalError, discover_policies, evaluate, prepare_input

# The flags that mean "give me the CI shape". Grouped here rather than checked inline so that adding
# one cannot accidentally leave the routing behind.
REPORTING_ARGS = ("inputKind", "statePath", "sha", "outputJson", "outputMarkdown", "commentMarker")


def wanted(args):
    """
    Whether this path should handle the invocation.

    Narrow on purpose. A single policy file with none of the reporting flags is the invocation every
    existing caller makes, and it must keep reaching the original code -- so this returns False for it
    even though this module could handle it perfectly well.
    """
    if any(getattr(args, name, None) for name in REPORTING_ARGS):
        return True
    # A directory or a glob. Previously this reached `open()` and failed with a bare "ERROR", so
    # handling it is new capability rather than changed behaviour.
    return not os.path.isfile(args.policyPath)


def run(args):
    """Evaluate every policy found, write the report, and return an exit status."""
    from ..status import ExitStatus

    policy_path = args.policyPath

    try:
        result = _evaluate(args, policy_path)
    except LocalError as e:
        log(f"ERROR: {e}")
        _write_failure(args, str(e))
        return ExitStatus.ERROR
    except KeyboardInterrupt:
        log("Interrupted")
        return ExitStatus.ERROR_CTRL_C

    if args.json:
        # The aggregate document, not the engine's -- there is no single engine document when several
        # policies ran. Only reachable once a reporting flag or a multi-policy path was asked for, so
        # no existing caller sees this instead of what it used to get.
        import json as _json

        print(_json.dumps(result, indent=2))

    log(result["headline"])

    if result["policies_errored"]:
        # "Could not evaluate" is tool health, not a policy decision, so it ignores --fail-on-error --
        # the same reason an unreachable platform does in `platform check`.
        log("Some policies could not be evaluated")
        return ExitStatus.ERROR

    verdict = result["verdict"]
    if verdict == "errored":
        return ExitStatus.ERROR
    if verdict == "failed" and args.failOnError:
        return ExitStatus.ERROR_POLICY_FAILED
    if verdict == "failed":
        log("Policies failed, but --fail-on-error was not set")
    if result.get("counts", {}).get("approval_required"):
        log("Some policies ask for approval; reported as a warning, which does not block")

    return ExitStatus.SUCCESS


def _evaluate(args, policy_path):
    policies = discover_policies(policy_path)
    if not policies:
        # A green result for a change nothing was evaluated against is the one outcome this must never
        # produce. "No policies found" is a configuration mistake, not a deliberate skip.
        raise LocalError(
            f"Nothing to evaluate: no policy files found at '{policy_path}'. Point -policy-path at a "
            "file, a directory or a glob containing tirith policies."
        )

    warnings = []

    with tempfile.TemporaryDirectory(prefix="tirith-local-") as scratch:
        input_path, redactions = prepare_input(
            args.inputPath,
            None,
            None,
            args.inputKind or "raw",
            os.path.dirname(args.inputPath) or ".",
            scratch,
            state_path=args.statePath,
        )
        if redactions:
            log(f"Masked {redactions} sensitive value(s) before evaluating")

        log(f"Evaluating {len(policies)} policy file(s) from '{policy_path}'")

        def on_unknown_enforcement(value):
            message = f"unrecognised meta.enforcement '{value}'; treating a failing policy as blocking"
            warnings.append(message)
            log(f"WARNING: {message}")

        policy_results, errored = evaluate(
            policies,
            input_path,
            on_unknown_enforcement=on_unknown_enforcement,
            var_paths=args.varPaths,
            inline_vars=args.inlineVars,
        )

    for path, reason in errored:
        log(f"WARNING: could not evaluate {path}: {reason}")

    counts, _findings = report.summarize(policy_results)
    evaluated_something = any(
        counts.get(key) for key in (report.PASS, report.FAIL, report.WARN, report.APPROVAL_REQUIRED, report.UNKNOWN)
    )

    # Every policy skipped means every check was swallowed by error_tolerance and nothing was actually
    # examined. This command has always called that a failure rather than a pass -- "None is not a
    # pass" -- and extending it must not quietly reverse that for a caller who passed a directory.
    #
    # Note this is a deliberate difference from `platform check`, which counts skips separately and
    # reports them as a pass. Both are defensible; what is not defensible is one surface silently
    # disagreeing with itself depending on how many policies you pointed it at.
    status = "COMPLETED"
    notes = None
    if not evaluated_something:
        status = "ERRORED"
        notes = [
            f"All {len(policies)} policy file(s) were skipped, so nothing was evaluated. Every check "
            "was swallowed by its error_tolerance -- usually because the resources the policies name "
            "are not in this document."
        ]

    result = report.result_document(
        "local",
        status,
        policy_results,
        policies_evaluated=len(policies),
        policies_errored=len(errored),
        policy_path=policy_path,
        policy_errors=[{"policy": path, "reason": reason} for path, reason in errored],
        policy_warnings=warnings,
    )

    write_output_json(args.outputJson, result)
    if args.outputMarkdown:
        write_output_markdown(
            args.outputMarkdown,
            report.render_markdown(
                policy_results,
                status,
                None,
                marker=args.commentMarker,
                limit=args.markdownLimit,
                commit=args.sha,
                notes=notes,
            ),
        )
    return result


def _write_failure(args, message):
    """
    Write both output files for a run that produced no verdict.

    A front end editing a sticky comment in place needs a marker-first body even here: writing nothing
    means it falls through to a body of its own with no marker, and PATCHing that over a good comment
    orphans it permanently.
    """
    result = report.result_document(
        "local",
        "ERRORED",
        {},
        policies_evaluated=0,
        policies_errored=0,
        policy_path=args.policyPath,
        policy_errors=[{"policy": None, "reason": message}],
    )
    write_output_json(args.outputJson, result)
    if args.outputMarkdown:
        write_output_markdown(
            args.outputMarkdown,
            report.render_markdown(
                {},
                "ERRORED",
                None,
                marker=args.commentMarker,
                limit=args.markdownLimit,
                commit=args.sha,
                notes=[message],
            ),
        )
    return result
