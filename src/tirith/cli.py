"""
CLI
"""

import argparse
import json
import logging
import sys
import textwrap

from tirith.logging import setup_logging
from tirith.prettyprinter import pretty_print_result_dict
from tirith.status import ExitStatus
from tirith import __version__

from .core import start_policy_evaluation

logger = logging.getLogger(__name__)


def eprint(*args, **kwargs):
    """
    Just like print() but prints to sys.stderr instead of stdout.
    Use it when printing error messages.
    """
    print(*args, file=sys.stderr, **kwargs)


# Subcommands are dispatched before the flat parser sees anything. argparse cannot express an
# optional subcommand alongside options like `-policy-path` (a single dash and a long name), and the
# local-evaluation surface is a contract: tests/core/test_output_compatibility.py asserts its --json
# output is byte-identical to a golden file. An explicit pre-dispatch leaves that untouched.
#
# Named `platform` because that is what it evaluates against: the policies your StackGuardian
# organization enforces, run on the platform, rather than policy files in your repository.
#
# It was briefly `remote` on this branch, on the argument that "platform check" can read as *a check of
# the platform*. Reverted -- the vagueness is minor next to having one name, and the concern that
# prompted the rename was really that the open-source surface could not gate at all, which
# `--fail-on-error` fixed. No alias in either direction: nothing is released, so there is no caller to
# keep working.
SUBCOMMAND = "platform"

# `ui` joins it on the same terms: dispatched before the flat parser, so the local-evaluation
# surface and its golden-file output are untouched. It is an optional extra -- it needs Python
# 3.9 and tirith supports 3.8 -- so tui/cli.py reports the missing extra rather than failing on
# an import here.
UI_SUBCOMMAND = "ui"
SUBCOMMANDS = {SUBCOMMAND, UI_SUBCOMMAND}


def main(args=None) -> ExitStatus:
    """
    The main function.

    Pre-process args, handle some special types of invocations,
    and run the main program with error handling.

    Return exit status code.
    """
    argv = list(sys.argv[1:] if args is None else args)

    if argv and argv[0] == UI_SUBCOMMAND:
        from tirith.tui import cli as tui_cli

        return tui_cli.main(argv)

    if argv and argv[0] in SUBCOMMANDS:
        from tirith.platform import cli as platform_cli

        return platform_cli.main(argv)

    try:

        class _WidthFormatter(argparse.RawTextHelpFormatter):
            def __init__(self, prog="PROG") -> None:
                super().__init__(prog, max_help_position=300)

        parser = argparse.ArgumentParser(
            description="Tirith (StackGuardian Policy Framework)",
            formatter_class=_WidthFormatter,
            epilog=textwrap.dedent(
                """\
         Subcommands:

            tirith platform check --help   Evaluate against the policies your StackGuardian
                                           organization enforces, rather than local files.
            tirith ui --help               Explore results, build policies and experiment in
                                           an interactive interface. Needs the 'tui' extra.

         About Tirith:
         
            * Abstract away the implementation complexity of policy engine underneath.
            * Simplify creation of declarative policies that are easy to read and interpret.
            * Provide a standard framework for scanning various configurations with granularity.
            * Provide modularity to enable easy extensibility
            * Github - https://github.com/StackGuardian/tirith
            * Docs - https://github.com/StackGuardian/tirith#readme
        """
            ),
        )
        parser.add_argument(
            "-policy-path",
            metavar="PATH",
            type=str,
            dest="policyPath",
            help="Path containing Tirith policy as code",
        )
        parser.add_argument(
            "-input-path",
            metavar="PATH",
            type=str,
            dest="inputPath",
            help="Input file path",
        )
        parser.add_argument(
            "-var-path",
            metavar="PATH",
            type=str,
            default=[],
            action="append",
            dest="varPaths",
            help="Variable file path(s)",
        )
        parser.add_argument(
            "-var",
            metavar="PATH",
            type=str,
            default=[],
            action="append",
            dest="inlineVars",
            help="Inline variable(s)",
        )
        parser.add_argument(
            "--json",
            dest="json",
            action="store_true",
            help="Only print the result in JSON form (useful for passing output to other programs)",
        )
        parser.add_argument(
            "--verbose",
            dest="verbose",
            action="store_true",
            help="Show detailed logs of from the run",
        )
        parser.add_argument(
            "--fail-on-error",
            dest="failOnError",
            action="store_true",
            help="Exit 3 when a policy fails, instead of 0. Off by default for compatibility.",
        )
        parser.add_argument("--version", action="version", version=__version__)

        # Everything below is additive, and off unless asked for. With none of it, this command
        # behaves exactly as it always has -- which matters because its `--json` stdout is a frozen
        # contract, pinned byte-for-byte by tests/core/test_output_compatibility.py.
        #
        # What they add is the shape a CI integration needs: many policies rather than one, the input
        # masked before its values reach a report, and the verdict written out as a document and a
        # markdown body for a front end to publish. Those are the same four files
        # `tirith platform check` writes, so a GitHub Action or a GitLab component can drive either
        # with one argv and one parser.
        reporting = parser.add_argument_group(
            "reporting", "Write the verdict out for a CI job to publish. All optional."
        )
        reporting.add_argument(
            "--input-kind",
            dest="inputKind",
            # A metavar, because the formatter aligns every option to the widest one and spelling the
            # choices out here pushed the whole help block far to the right.
            metavar="KIND",
            choices=("terraform_plan", "terraform_state", "kubernetes", "json"),
            default=None,
            # Masking is opt-in because it changes the evaluator messages, and those messages are
            # the frozen --json output. Omitted, the file is read exactly as it always has been.
            help="terraform_plan, terraform_state, kubernetes or json. Masks the input before evaluating",
        )
        reporting.add_argument(
            "--state-path",
            metavar="PATH",
            dest="statePath",
            default=None,
            help="Terraform state, when --input-kind is terraform_state",
        )
        reporting.add_argument(
            "--sha",
            metavar="SHA",
            dest="sha",
            default=None,
            help="Revision these findings describe, recorded in the report",
        )
        reporting.add_argument(
            "--output-json",
            metavar="PATH",
            dest="outputJson",
            default=None,
            help="Write the result document here (same shape as `tirith platform check`)",
        )
        reporting.add_argument(
            "--output-markdown",
            metavar="PATH",
            dest="outputMarkdown",
            default=None,
            help="Write a markdown report here, for a comment or a note",
        )
        reporting.add_argument(
            "--comment-marker",
            metavar="TEXT",
            dest="commentMarker",
            default=None,
            help="Opaque first line of the markdown, for comment stickiness",
        )
        reporting.add_argument(
            "--markdown-limit",
            metavar="N",
            type=int,
            dest="markdownLimit",
            default=60000,
            help="Truncate the markdown to this length. Default: 60000",
        )

        args = parser.parse_args(argv)

        if not argv:
            parser.print_help()
            sys.exit(0)

        if not args.policyPath:
            eprint("'-policy-path' argument is required")
            eprint("-policy-path argument is required. Provide a path to SG policy")
            return ExitStatus.ERROR
        if not args.inputPath:
            eprint("Path to input file should be provided to '--input-path' argument")
            eprint(
                "-input-path argument is required. Provide a path to JSON file compatible with the provider defined in the SG policy"
            )
            return ExitStatus.ERROR

        if args.json:
            # Disable all logging output
            logging.disable(logging.CRITICAL)
        else:
            setup_logging(verbose=args.verbose)

        # The aggregate path: many policies, or any of the reporting flags. A single policy file with
        # none of them falls through to the original code below, byte-for-byte -- which is what keeps
        # the frozen --json contract frozen, and every existing caller unaffected.
        from tirith.local import check as local_check

        if local_check.wanted(args):
            return local_check.run(args)

        try:
            result = start_policy_evaluation(args.policyPath, args.inputPath, args.varPaths, args.inlineVars)

            if args.json:
                formatted_result = json.dumps(result, indent=3)
                print(formatted_result)
            else:
                pretty_print_result_dict(result)

            # Without --fail-on-error this returns 0 whether the policy passed or failed, which is
            # what it has always done: the verdict is in the output, and changing that silently would
            # turn every existing green CI job red on upgrade.
            #
            # But a gate that cannot fail is not a gate, and this was the only way to run tirith
            # without an account -- so the honest answer was an opt-in flag rather than pointing
            # people at the hosted path when they need an exit code that means something.
            #
            # 3, not 1, and the distinction is the point: 3 says the infrastructure violates a policy,
            # 1 says tirith could not tell you. The same split `platform check` uses, because a caller
            # scripting both should not have to learn two vocabularies.
            #
            # `final_result` is tri-state, and that is what decides:
            #
            #   True    every check that ran passed              -> 0
            #   False   a check ran and said no                  -> 3
            #   None    nothing ran; every check was skipped     -> 1
            #   absent  the policy could not be loaded at all    -> 1
            #
            # None is not a pass. A policy whose every check was skipped -- `error_tolerance` swallowing
            # a provider that found nothing -- checked precisely nothing, and reporting that as green is
            # the failure this whole flag exists to prevent. `absent` is the missing-variables path,
            # which returns `errors` and no result at all.
            #
            # `errors` is deliberately NOT consulted. It reads like a tool-failure signal and is not: it
            # is populated only by the eval-expression pass, and the one thing that puts a message there
            # beside a real verdict is the informational "these ids are not defined and have been
            # removed" note. Gating on it inverted both halves of this contract -- a genuine violation
            # whose expression mentioned a typo'd id exited 1, while a policy naming an unknown provider
            # exited 3.
            #
            # Known limit, worth stating rather than pretending otherwise: a *misconfigured* policy -- an
            # unsupported `condition.type`, an unknown `required_provider` -- surfaces from the engine as
            # an ordinary failed evaluator with no error attached, so it is indistinguishable from a
            # violation here and exits 3. Fixing that means the engine reporting it distinctly, not this
            # branch guessing from free text.
            if args.failOnError:
                final_result = result.get("final_result")
                if "final_result" not in result or final_result is None:
                    return ExitStatus.ERROR
                if final_result is not True:
                    return ExitStatus.ERROR_POLICY_FAILED
            return ExitStatus.SUCCESS
        except Exception as e:
            # TODO:write an exception class for all provider exceptions.
            if args.json:
                # Print empty JSON
                print("{}")
            else:
                logger.exception(e)
                eprint("ERROR")
            return ExitStatus.ERROR

        # TODO: move to core
        # if not args.inputType:
        #     print("'--input-type' argument is required")
        #     return ExitStatus.ERROR

        # inputType = args.inputType

    except KeyboardInterrupt:
        eprint("\nFailed because of Keyboard Interrupt")
        return ExitStatus.ERROR_CTRL_C
    except SystemExit as e:
        if e.code != ExitStatus.SUCCESS:
            eprint("\nFailed because of System Exit")
            return ExitStatus.ERROR
    except Exception as e:
        # TODO: Further distinction between expected and unexpected errors.
        eprint(f"\n {type(e)}: {str(e)}")
        eprint("\nFailed because of an unhandled exception")
        return ExitStatus.ERROR
