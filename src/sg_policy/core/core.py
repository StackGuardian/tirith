import logging

from .evaluators import *
from pathlib import Path
import json
import ast

from ..providers.infracost import provide as infracost_provider
from ..providers.terraform_plan import provide as terraform_provider
from ..providers.sg_workflow import provide as sg_wf_provider

# TODO: Use __name__ for the logger name instead of using the root logger
logger = logging.getLogger()


def get_evaluator_inputs_from_provider_inputs(provider_inputs, provider_module, input_data):
    # TODO: Get the inputs from given providers
    if provider_module == "terraform_plan":
        return terraform_provider(provider_inputs, input_data)
    if provider_module == "infracost":
        return infracost_provider(provider_inputs, input_data)
    if provider_module == "sg_workflow":
        return sg_wf_provider(provider_inputs, input_data)


def generate_evaluator_result(evaluator_obj, input_data, provider_module):

    provider_inputs = evaluator_obj.get("provider_args")
    condition = evaluator_obj.get("condition")
    evaluator_class = condition.get("type")
    evaluator_data = condition.get("expected")
    eval_id = evaluator_obj.get("id")

    evaluator_inputs = get_evaluator_inputs_from_provider_inputs(
        provider_inputs, provider_module, input_data
    )  # always an array of inputs for evaluators
    result = {
        "id": eval_id,
        "passed": False,
    }
    try:
        evaluator_instance = ast.literal_eval(f"{evaluator_class}()")
    except NameError as e:
        print(f"{evaluator_class} is not a supported evaluator")
    evaluation_results = []
    has_evaluation_passed = True
    for evaluator_input in evaluator_inputs:
        evaluation_result = evaluator_instance.evaluate(evaluator_input["value"], evaluator_data)
        evaluation_result["meta"] = evaluator_input.get("meta")
        evaluation_results.append(evaluation_result)
        if not evaluation_result["passed"]:
            has_evaluation_passed = False
    result["result"] = evaluation_results
    result["passed"] = has_evaluation_passed
    return result


def final_evaluator(eval_string, evalIdValues):
    for key in evalIdValues:
        eval_string = eval_string.replace(key, str(evalIdValues[key]["passed"]))
        # print (eval_string)
    # TODO: shall we use and, or and not instead of symbols?
    eval_string = eval_string.replace(" ", "").replace("&&", " and ").replace("||", " or ").replace("!", " not ")
    return ast.literal_eval(eval_string)


# print(final_evaluator("(!(pol_check_1  &&  pol_check_2)  && pol_check_3 ) && pol_check_4", {
# 	"pol_check_1":False,
# 	"pol_check_2":True,
# 	"pol_check_3":True,
# 	"pol_check_4":False
# 	}))

# sg_policy --policy-path "F:\StackGuardian\policy-framework\tests\providers\policy.json" --input-path "F:\StackGuardian\policy-framework\tests\providers\input.json"


def start_policy_evaluation(policy_path, input_path):

    with open(policy_path) as json_file:
        policy_data = json.load(json_file)
    # TODO: validate policy_data against schema

    with open(input_path) as json_file:
        input_data = json.load(json_file)
    # TODO: validate input_data using the optionally available validate function in provider

    policy_meta = policy_data.get("meta")
    eval_objects = policy_data.get("evaluators")
    final_evaluation_policy_string = policy_data.get("eval_expression")
    provider_module = policy_meta.get("required_provider", "core")
    # TODO: Write functionality for dynamically importing evaluators from other modules.
    eval_results = {}
    for eval_obj in eval_objects:
        eval_id = eval_obj.get("id")
        logger.info(f"Processing evaluator '{eval_id}'")
        eval_results[eval_id] = generate_evaluator_result(eval_obj, input_data, provider_module)
    final_evaluation_result = final_evaluator(final_evaluation_policy_string, eval_results)

    final_output = {
        "meta": {"version": policy_meta.get("version"), "required_provider": provider_module},
        "final_result": final_evaluation_result,
        "evaluators": eval_results,
    }
    return final_output
