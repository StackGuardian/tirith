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
from sg_policy.status import ExitStatus

from .core import start_policy_evaluation

# TODO: Use at least __name__ for the logger name
logger = logging.getLogger()


def main(args=None) -> ExitStatus:
    """
    The main function.

    Pre-process args, handle some special types of invocations,
    and run the main program with error handling.

    Return exit status code.
    """
    try:
        parser = argparse.ArgumentParser(
            description="StackGuardian Policy Framework.",
            formatter_class=argparse.RawTextHelpFormatter,
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

        if not args.policyPath:
            sys.stderr.write("'-policy-path' argument is required")
            sys.stderr.write("-policy-path argument is required. Provide a path to SG policy")
            return ExitStatus.ERROR
        if not args.inputPath:
            sys.stderr.write("Path to input file should be provided to '--input-path' argument")
            sys.stderr.write(
                "-input-path argument is required. Provide a path to JSON file compatible with the provider defined in the SG policy"
            )
            return ExitStatus.ERROR

        if not args.json:
            setup_logging(verbose=args.verbose)

        try:
            result = start_policy_evaluation(args.policyPath, args.inputPath)
            formatted_result = json.dumps(result, indent=3)
            sys.stdout.write(formatted_result)
        except Exception as e:
            # TODO:write an exception class for all provider exceptions.
            if args.json:
                # Print empty JSON
                sys.stdout.write("{}")
            else:
                logger.exception(e)
                sys.stderr.write("ERROR")
            return ExitStatus.ERROR

        # TODO: move to core
        # if not args.inputType:
        #     print("'--input-type' argument is required")
        #     return ExitStatus.ERROR

        # inputType = args.inputType

    except KeyboardInterrupt:
        sys.stderr.write("\nFailed because of Keyboard Interrupt")
        return ExitStatus.ERROR_CTRL_C
    except SystemExit as e:
        if e.code != ExitStatus.SUCCESS:
            sys.stderr.write("\nFailed because of System Exit")
            return ExitStatus.ERROR
    except Exception as e:
        # TODO: Further distinction between expected and unexpected errors.
        sys.stderr.write(f"\n {type(e)}: {str(e)}")
        sys.stderr.write("\nFailed because of an unhandled exception")
        return ExitStatus.ERROR
