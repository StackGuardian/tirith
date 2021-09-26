#!/usr/bin/env python

import os
import sys
import json
from subprocess import Popen, PIPE, check_output

# with open('out.json') as out:
#    evalResults = json.load(out)


def evaluate_type(value, eval_type, evaluation_condition):
    fail_set = False

    for res in value[eval_type]:
        eval_pass = res["evaluation_result"]["pass"]
        message = res["evaluation_result"]["message"]
        evaluation = True if eval_pass else False

        # all_evaluations[eval_type]['evaluations'][evaluation] = \
        #        message if evaluation in all_evaluations[eval_type]['evaluations'] else [message]
        if evaluation not in all_evaluations[eval_type]["evaluations"]:
            all_evaluations[eval_type]["evaluations"][evaluation] = []

        all_evaluations[eval_type]["evaluations"][evaluation].append(message)

        outputs[eval_type].append(res)

        if eval_pass != True:
            not_true[eval_type].append(res)
            if eval_pass == False:
                errors[eval_type].append(res)

        # if res['evaluation_result']['pass'] == evaluation_condition:
        #    all_evaluations[eval_type]['all_pass'] = False
        # print(eval_type, res['evaluation_result']['pass'] is not evaluation_condition)
        if (
            res["evaluation_result"]["pass"] is not evaluation_condition
            and not fail_set
        ):
            # all_evaluations[eval_type]['all_pass'] = not evaluation_condition
            all_evaluations[eval_type]["all_pass"] = not all_evaluations[eval_type][
                "all_pass"
            ]
            fail_set = True


def run_cmds(cmds, cwd=None, env=None, stdout=sys.stdout, stderr=PIPE):
    p = Popen(cmds, cwd, env, stdout=stdout, stderr=stderr)
    return p.communicate()


def evaluate(data_file, input_file):
    if os.path.isfile("main.rego"):
        # opa eval --fail --format json --data main.rego 'data.stackguardian.terraform_plan.main.evaluators' --data
        opa_command = [
            "opa",
            "eval",
            "--fail",
            "--format",
            "json",
            "--data",
            "rego/main.rego",
            "data",
            "--data",
            data_file,
            "--input",
            input_file,
        ]
        output, _ = run_cmds(opa_command, stdout=PIPE, stderr=sys.stdout)

        opa_args = "data.stackguardian.terraform_plan.main.evaluators"
        opa_args_list = "".join([f"['{arg}']" for arg in opa_args.split(".")[1:-1]])

        if output:
            output_json = json.loads(str(output, "utf-8"))

            if not output_json.get("errors"):
                if output_json.get("result"):
                    for res in output_json["result"]:
                        for exp in res["expressions"]:
                            # value = exp['value']
                            value = eval(f"exp['value']{opa_args_list}")

                            for eval_type in value:
                                if eval_type.endswith("_of"):
                                    errors[eval_type] = []
                                    outputs[eval_type] = []
                                    not_true[eval_type] = []
                                    all_evaluations[eval_type] = {
                                        "evaluations": {},
                                        "all_pass": False
                                        if eval_type == "any_of"
                                        else True,
                                    }

                                    # evaluation_condition = True if output_json == "any_of" else False
                                    evaluation_condition = (
                                        True if output_json == "all_of" else False
                                    )
                                    evaluate_type(
                                        value, eval_type, evaluation_condition
                                    )

                            log = {
                                "errors": errors,
                                "outputs": outputs,
                                "all_not_true_evaluations": not_true,
                            }

                            print(json.dumps(log, indent=1))
                            # print('\nUser readable part:\n')

                            all_pass = [
                                all_evaluations[p]["all_pass"] for p in all_evaluations
                            ]
                            print(
                                f'\n\nAll evaluations have {"not" if False in all_pass else ""} passed.'
                            )

                            for eval_type, report in all_evaluations.items():
                                if report["evaluations"]:
                                    status = (
                                        "been successfull"
                                        if report["all_pass"]
                                        else "failed"
                                    )
                                    print(
                                        f'\nEvaluation of {" ".join(eval_type.split("_")).upper()} conditions has {status}:'
                                    )
                                    print(
                                        "======================================================"
                                    )

                                    successes = report["evaluations"].get(True)
                                    fails = report["evaluations"].get(False)

                                    if successes:
                                        if isinstance(successes, list):
                                            for success in successes:
                                                if success:
                                                    print(f"PASS: {success}")
                                        else:
                                            print(f"PASS: {successes}")

                                    if fails:
                                        for fail in fails:
                                            print(f"FAIL: {fail}")
    else:
        print(
            "You are in the wrong directory!\nYou need to run the script from directory that contains main.rego."
        )


errors = {}
outputs = {}
not_true = {}
all_evaluations = {}

if __name__ == "__main__":
    if len(sys.argv) == 3:
        data_json, input_json = sys.argv[1:]
        if os.path.isfile(data_json) and os.path.isfile(input_json):
            evaluate(data_json, input_json)
