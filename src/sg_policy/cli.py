"""
CLI
"""

import argparse
import json
import logging
import sys
import textwrap

import sg_policy.providers.terraform_plan.handler as python_tf_plan_handler
from sg_policy.logging import setup_logging
from sg_policy.prettyprinter import pretty_print_result_dict
from sg_policy.status import ExitStatus

from .core import start_policy_evaluation

# TODO: Use at least __name__ for the logger name
logger = logging.getLogger()


def eprint(*args, **kwargs):
    """
    Just like print() but prints to sys.stderr instead of stdout.
    Use it when printing error messages.
    """
    print(*args, file=sys.stderr, **kwargs)


def main(args=None) -> ExitStatus:
    """
    The main function.

    Pre-process args, handle some special types of invocations,
    and run the main program with error handling.

    Return exit status code.
    """
    try:

        class _WidthFormatter(argparse.RawTextHelpFormatter):
            def __init__(self, prog="PROG") -> None:
                super().__init__(prog, max_help_position=300)

        parser = argparse.ArgumentParser(
            description="StackGuardian Policy Framework.",
            formatter_class=_WidthFormatter,
            epilog=textwrap.dedent(
                """\
         About StackGuardian Policy Framework:
         
                                * Abstract away the implementation complexity of policy engine underneath.
                                * Simplify creation of declarative policies that are easy to read and interpret.
                                * Provide a standard framework for scanning various configurations with granularity.
                                * Provide modularity to enable easy extensibility
                                * Github - https://github.com/StackGuardian/policy-framework
                                * Docs - https://docs.stackguardian.io/docs/policy-framework/overview
         """
            ),
        )
        parser.add_argument(
            "-policy-path",
            metavar="PATH",
            type=str,
            dest="policyPath",
            help="Path containing policy defined using StackGuardian Policy Framework",
        )
        parser.add_argument(
            "-input-path",
            metavar="SOURCE-TYPE",
            type=str,
            dest="inputPath",
            help="Input file path",
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
        parser.add_argument("--version", action="version", version="1.0.0-alpha.1")

        args = parser.parse_args()

        if len(sys.argv) == 1:
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
            result = start_policy_evaluation(args.policyPath, args.inputPath)

            if args.json:
                formatted_result = json.dumps(result, indent=3)
                print(formatted_result)
            else:
                pretty_print_result_dict(result)
            return ExitStatus.SUCCESS
        except Exception as e:
            # TODO:write an exception class for all provider exceptions.
            if args.json:
                # Print empty JSON
                print(json.dumps({"errors": str(e)}))
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
