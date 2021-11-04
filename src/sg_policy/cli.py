"""
CLI
"""

import argparse
import sys

from sg_policy.status import ExitStatus
#import sg_policy.providers as providers
import sg_policy.providers.opa.terraform_plan.handler as handler


def main(args=None) -> ExitStatus:
    """
    The main function.

    Pre-process args, handle some special types of invocations,
    and run the main program with error handling.

    Return exit status code.
    """
    try:
        parser = argparse.ArgumentParser(description="StackGuardian Policy Framework.")
        parser.add_argument(
            "--policy-policyPath",
            metavar="PATH",
            type=str,
            dest="policyPath",
            help="Path containing policy defined using SG Policy Framework",
        )
        parser.add_argument(
            "--input-type",
            metavar="SOURCE-TYPE",
            type=str,
            dest="inputType",
            help="Input config type to be evaluted. Example: terraform_plan, terraform_hcl, cloudformation_json",
        )
        parser.add_argument(
            "--input-path",
            metavar="SOURCE-TYPE",
            type=str,
            dest="inputPath",
            help="Input config path. Can be a file or dir, depending on --input-type",
        )
        parser.add_argument(
            "--tf-version",
            metavar="TF-VERSION",
            type=str,
            dest="tfVersion",
            help="Terraform version for the provided source. Example: 0.14.6, 1.0.0",
        )
        args = parser.parse_args()

        if not args.policyPath:
            print("'--policyPath' argument is required")
            return ExitStatus.ERROR
        if not args.inputType:
            print("'--input-type' argument is required")
            return ExitStatus.ERROR

        inputType = args.inputType

        if inputType == "terraform_plan":
            if not args.inputPath:
                print(
                    "Path to terraform plan file should be provided to '--input-path' argument"
                )
                return ExitStatus.ERROR
            if not args.tfVersion:
                print(
                    "'--tf-version' argument is required when --input-type=terraform_plan"
                )
                return ExitStatus.ERROR
            #providers.opa.terraform_plan.handler(
            #    args.policyPath, args.inputPath, args.tfVersion
            #)
            handler.evaluate(args.policyPath, args.inputPath)
            # print(
            #     f"Policy template successfully generated and stored in {args.policyPath.rsplit('/',1)[0]}/policy_template.json")
        elif inputType in ["terraform_hcl", "cloudformation_json"]:
            print(
                "Provided input type is not supported yet. Only 'terraform_plan' is supported at the moment."
            )
            return ExitStatus.ERROR
        else:
            print("Unsupported --input-type specified.")
            return ExitStatus.ERROR
        return ExitStatus.SUCCESS
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
        sys.stderr.write("\nFailed because of an unhandled exception.")
        return ExitStatus.ERROR
