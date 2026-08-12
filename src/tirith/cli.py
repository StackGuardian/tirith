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
# `remote` names the distinction that actually exists: the policies and the evaluation live somewhere
# else. `platform` was internal vocabulary escaping into a user-facing verb -- it reads in English as
# "check the platform", which is what `--platform` means in most tools a reader has used.
SUBCOMMAND = "remote"

# `platform` still dispatches, undocumented, because snippets carrying it exist. Not in the help, not
# in the README: two documented names for one command is how the vagueness complaint arrives twice.
DEPRECATED_SUBCOMMANDS = {"platform": SUBCOMMAND}

SUBCOMMANDS = {SUBCOMMAND, *DEPRECATED_SUBCOMMANDS}


def main(args=None) -> ExitStatus:
    """
    The main function.

    Pre-process args, handle some special types of invocations,
    and run the main program with error handling.

    Return exit status code.
    """
    argv = list(sys.argv[1:] if args is None else args)

    if argv and argv[0] in SUBCOMMANDS:
        from tirith.platform import cli as remote_cli

        if argv[0] in DEPRECATED_SUBCOMMANDS:
            replacement = DEPRECATED_SUBCOMMANDS[argv[0]]
            eprint(f"'tirith {argv[0]}' is deprecated; use 'tirith {replacement}'.")
            argv = [replacement, *argv[1:]]

        return remote_cli.main(argv)

    try:

        class _WidthFormatter(argparse.RawTextHelpFormatter):
            def __init__(self, prog="PROG") -> None:
                super().__init__(prog, max_help_position=300)

        parser = argparse.ArgumentParser(
            description="Tirith (StackGuardian Policy Framework)",
            formatter_class=_WidthFormatter,
            epilog=textwrap.dedent("""\
         Subcommands:

            tirith remote check --help     Evaluate against the policies your StackGuardian
                                          organization enforces, rather than local files.

         About Tirith:
         
            * Abstract away the implementation complexity of policy engine underneath.
            * Simplify creation of declarative policies that are easy to read and interpret.
            * Provide a standard framework for scanning various configurations with granularity.
            * Provide modularity to enable easy extensibility
            * Github - https://github.com/StackGuardian/tirith
            * Docs - https://github.com/StackGuardian/tirith#readme
        """),
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
            # 1 says tirith could not tell you. The same split `remote check` uses, because a caller
            # scripting both should not have to learn two vocabularies.
            #
            # Which means `final_result` alone is not enough to decide. It is False both for a policy
            # that genuinely failed and for one that could not be evaluated -- an unparseable
            # eval_expression, or an operator the evaluator does not implement -- and those are not the
            # same answer. `errors` is what separates them; the missing-variables path returns errors
            # and no `final_result` key at all, so absence is treated the same way.
            if args.failOnError:
                if result.get("errors") or "final_result" not in result:
                    return ExitStatus.ERROR
                if result["final_result"] is not True:
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
