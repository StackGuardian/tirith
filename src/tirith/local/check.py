"""
Orchestration for `tirith local check`.

Lifted from the GitHub Action's `run_local`, with the GitHub-specific parts left behind. Writes the
same two files `tirith platform check` writes -- the result document and the report body -- so
everything a front end does downstream is identical in both modes.
"""

import tempfile

from ..platform import report
from ..platform.check import log, write_output_json, write_output_markdown
from .evaluate import LocalError, discover_policies, evaluate, prepare_input


def write_failure_report(opts, message):
    """
    Write both output files for a run that produced no verdict.

    These paths used to return without writing either file, so a front end fell through to a
    marker-less body and destroyed its own sticky comment. Writing both keeps the comment findable
    and, more usefully, puts the reason on the merge request instead of only in the job log.
    """
    result = report.result_document(
        "local",
        "ERRORED",
        {},
        policies_evaluated=0,
        policies_errored=0,
        policy_path=opts.policy_path,
        policy_errors=[{"policy": None, "reason": message}],
    )
    write_output_json(opts.output_json, result)
    write_output_markdown(
        opts.output_markdown,
        report.render_markdown(
            {},
            "ERRORED",
            None,
            marker=opts.comment_marker,
            limit=opts.markdown_limit,
            commit=opts.sha,
            notes=[message],
        ),
    )
    return result


def run_check(opts):
    """
    Evaluate the policy files at `--policy-path` and write the report. Raises LocalError.

    The scratch directory holds the masked document. It is a temporary directory rather than
    somewhere under --source-dir, so that a caller who later packs its source tree cannot ship the
    document we wrote beside the one the user committed.
    """
    policies = discover_policies(opts.policy_path)
    if not policies:
        # The one outcome this whole mode must never produce is a green result for a change nothing
        # was evaluated against. "No policies found" is not a skip.
        raise LocalError(
            f"Nothing to evaluate: no policy files found at '{opts.policy_path}'. Point "
            "--policy-path at a file, a directory or a glob containing tirith policies."
        )

    if opts.infracost_path:
        # Cost policies need the platform: local mode evaluates one document, and infracost output
        # is a second one. Saying so beats evaluating the plan and reporting a cost policy as
        # unevaluated with no explanation.
        log(
            "WARNING: --infracost-path is ignored in local mode, which evaluates a single "
            "document. Cost policies need `tirith platform check`."
        )

    warnings = []

    with tempfile.TemporaryDirectory(prefix="tirith-local-") as scratch:
        input_path, redactions = prepare_input(
            opts.input_path,
            opts.plan_file,
            opts.terraform_bin,
            opts.input_kind,
            opts.source_dir,
            scratch,
            state_path=opts.state_path,
        )
        if redactions:
            log(f"Masked {redactions} sensitive value(s) before evaluating")

        log(f"Evaluating {len(policies)} policy file(s) from '{opts.policy_path}'")

        def on_unknown_enforcement(value):
            message = f"unrecognised meta.enforcement '{value}'; treating a failing policy as blocking"
            warnings.append(message)
            log(f"WARNING: {message}")

        policy_results, errored = evaluate(policies, input_path, on_unknown_enforcement=on_unknown_enforcement)

    for path, reason in errored:
        log(f"WARNING: could not evaluate {path}: {reason}")

    # Rendered as a completed evaluation on purpose. Results genuinely were produced, and the
    # renderer's ERRORED narrative ("the workflow run finished as ERRORED without producing policy
    # results") would be simply untrue here. A policy that could not be evaluated is already a
    # visible FAIL carrying its own reason, and the exit code is what actually gates.
    result = report.result_document(
        "local",
        "COMPLETED",
        policy_results,
        policies_evaluated=len(policies),
        policies_errored=len(errored),
        policy_path=opts.policy_path,
        policy_errors=[{"policy": path, "reason": reason} for path, reason in errored],
        policy_warnings=warnings,
    )

    write_output_json(opts.output_json, result)
    write_output_markdown(
        opts.output_markdown,
        report.render_markdown(
            policy_results,
            "COMPLETED",
            None,
            marker=opts.comment_marker,
            limit=opts.markdown_limit,
            commit=opts.sha,
        ),
    )

    log(result["headline"])
    return result
