"""
`tirith local check` -- evaluate policy files committed in your repository, with no credentials.

A sibling of `tirith platform check` rather than a flag on it. `platform check` masks, packs,
uploads, runs on StackGuardian and polls; a path that does none of those things under the same verb
would make its help text wrong for half its readers. Mechanically it would be worse still:
`--workflow-id` is required there, so a flag would have to lift that requirement out of argparse
into a hand-rolled conditional, weakening the platform path to accommodate a mode with no workflows.

Local mode is also never entered implicitly. `platform check` with no credentials stays a hard error,
and a caller wanting "no credentials therefore local" implements that itself -- a front end that
guesses wrong evaluates whatever happens to be committed and reports green, which is exactly the
outcome a policy gate exists to prevent.

Every identity, workflow, archive and run flag is deliberately absent rather than accepted and
ignored: a credential-shaped flag silently doing nothing in a credential-free mode is how someone
ends up with a green check their organization's policies never saw.
"""

import argparse

from ..platform.check import log
from ..status import ExitStatus
from .check import run_check, write_failure_report
from .evaluate import LocalError

INPUT_KINDS = ("terraform_plan", "terraform_state", "kubernetes", "json")

DEFAULT_POLICY_PATH = ".tirith/policies"


def build_parser():
    parser = argparse.ArgumentParser(
        prog="tirith local",
        description="Evaluate policy files committed in your repository. Talks to nothing.",
    )
    sub = parser.add_subparsers(dest="subcommand")

    check = sub.add_parser(
        "check",
        help="Evaluate committed policy files against a document and report the verdict.",
        description=(
            "Masks the document, evaluates every policy found at --policy-path, and writes the same "
            "result document and markdown report that `tirith platform check` writes. Requires no "
            "credentials and makes no network calls."
        ),
    )

    policies = check.add_argument_group("policies")
    policies.add_argument(
        "--policy-path",
        default=DEFAULT_POLICY_PATH,
        help=(
            "A policy file, a directory, or a glob. A directory is searched recursively for "
            f"*.tirith.json, or failing that for any .json file shaped like a policy. Default: "
            f"{DEFAULT_POLICY_PATH}"
        ),
    )

    inputs = check.add_argument_group("inputs")
    inputs.add_argument("--input-path", default=None, help="Document to evaluate. Default: plan.json or tfplan.json.")
    inputs.add_argument(
        "--plan-file", default=None, help="Binary terraform plan, rendered in memory. Not with --input-path."
    )
    inputs.add_argument("--terraform-bin", default=None, help="terraform/tofu binary used for --plan-file.")
    inputs.add_argument("--input-kind", default="terraform_plan", choices=INPUT_KINDS, help="What the document is.")
    inputs.add_argument("--state-path", default=None, help="Terraform state, when --input-kind is terraform_state.")
    inputs.add_argument(
        "--infracost-path",
        default=None,
        help="Accepted and ignored: cost policies need a second document, so they need platform mode.",
    )
    inputs.add_argument("--source-dir", default=".", help="Where to look for the document. Default: .")

    run = check.add_argument_group("run")
    run.add_argument("--sha", default=None, help="Revision these findings describe, recorded in the report.")

    output = check.add_argument_group("output")
    output.add_argument("--output-json", default=None, help="Write the result document here.")
    output.add_argument("--output-markdown", default=None, help="Write a markdown report here.")
    output.add_argument("--comment-marker", default=None, help="Opaque first line of the markdown, for stickiness.")
    output.add_argument("--markdown-limit", type=int, default=60000, help="Truncate the markdown to this length.")
    output.add_argument(
        "--fail-on-error",
        action="store_true",
        help=(
            "Exit non-zero when a policy fails. A policy that could not be evaluated at all always "
            "exits non-zero regardless of this flag."
        ),
    )

    return parser


def main(argv):
    parser = build_parser()
    opts = parser.parse_args(argv[1:])

    if opts.subcommand != "check":
        parser.print_help()
        return ExitStatus.SUCCESS

    try:
        result = run_check(opts)
    except LocalError as e:
        # Fails closed, and leaves a report behind: a front end editing a sticky comment in place
        # needs a marker-first body even on this path, or it orphans the comment it was updating.
        log(f"ERROR: {e}")
        write_failure_report(opts, str(e))
        return ExitStatus.ERROR
    except KeyboardInterrupt:
        log("Interrupted")
        return ExitStatus.ERROR_CTRL_C

    # "Could not evaluate" is tool health, not a policy decision, so it ignores --fail-on-error
    # exactly as an unreachable platform does in the other mode.
    if result["policies_errored"]:
        log("Some policies could not be evaluated")
        return ExitStatus.ERROR

    verdict = result["verdict"]
    if verdict == "errored":
        log("The evaluation did not produce a verdict")
        return ExitStatus.ERROR
    if verdict == "failed" and opts.fail_on_error:
        return ExitStatus.ERROR_POLICY_FAILED
    if verdict == "failed":
        log("Policies failed, but --fail-on-error was not set")
    if result.get("counts", {}).get("approval_required"):
        log("Some policies ask for approval; reported as a warning, which does not block")

    return ExitStatus.SUCCESS
