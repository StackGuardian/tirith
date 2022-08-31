"""
CLI
"""

import argparse
import sys
import textwrap
import simplejson as json
from sg_policy.logging import setup_logging
from sg_policy.status import ExitStatus
import logging


from .core import start_policy_evaluation

# import sg_policy.providers as providers
import sg_policy.providers.terraform_plan.handler as python_tf_plan_handler

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
            "--policy-path",
            metavar="PATH",
            type=str,
            dest="policyPath",
            help="Path containing policy defined using SG Policy Framework",
        )
        parser.add_argument(
            "--input-path",
            metavar="SOURCE-TYPE",
            type=str,
            dest="inputPath",
            help="Input config path. Can be a file or dir, depending on --input-type",
        )
        parser.add_argument(
            "--json",
            dest="json",
            action="store_true",
            help="Just print the result in JSON form (useful for passing to other programs)",
        )
        parser.add_argument(
            "--verbose",
            dest="verbose",
            action="store_true",
            help="Show detailed logs of the program run",
        )
        parser.add_argument("--version", action="version", version="1.0.0-alpha.1")

        args = parser.parse_args()

        if not args.policyPath:
            print("'--policyPath' argument is required")
            return ExitStatus.ERROR
        if not args.inputPath:
            print("Path to input file should be provided to '--input-path' argument")
            return ExitStatus.ERROR

        if not args.json:
            setup_logging(verbose=args.verbose)

        try:
            result = start_policy_evaluation(args.policyPath, args.inputPath)
            formatted_result = json.dumps(result, indent=3)
            print(formatted_result)
        except Exception as e:
            # TODO:write an exception class for all provider exceptions.
            logger.exception(e)
            print("ERROR")
            return ExitStatus.ERROR

        # TODO: move to core
        # if not args.inputType:
        #     print("'--input-type' argument is required")
        #     return ExitStatus.ERROR

        # inputType = args.inputType

        # if inputType == "terraform_plan":
        #     if not args.inputPath:
        #         # TODO:check if the input and policy path exists.
        #         print(
        #             "Path to terraform plan file should be provided to '--input-path' argument"
        #         )
        #         return ExitStatus.ERROR
        #     if not args.tfVersion:
        #         print(
        #             "'--tf-version' argument is required when --input-type=terraform_plan"
        #         )
        #         return ExitStatus.ERROR
        #     # providers.opa.terraform_plan.handler(
        #     #    args.policyPath, args.inputPath, args.tfVersion
        #     # )
        #
        #     try:
        #         result = start_policy_evaluation(args.policyPath, args.inputPath)
        #         print(result)
        #     except:
        #         # TODO:write an exception class for all provider exceptions.
        #         print("ERROR")
        #         return ExitStatus.ERROR
        #     # print(
        #     #     f"Policy template successfully generated and stored in {args.policyPath.rsplit('/',1)[0]}/policy_template.json")
        # elif inputType in ["terraform_hcl", "cloudformation_json"]:
        #     print(
        #         "Provided input type is not supported yet. Only 'terraform_plan' is supported at the moment."
        #     )
        #     return ExitStatus.ERROR
        # else:
        #     print("Unsupported --input-type specified.")
        #     return ExitStatus.ERROR
        # return ExitStatus.SUCCESS
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
