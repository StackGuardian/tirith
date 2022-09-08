import ast
import json
import logging
from pathlib import Path

from ..providers.infracost import provide as infracost_provider
from ..providers.sg_workflow import provide as sg_wf_provider
from ..providers.terraform_plan import provide as terraform_provider
from .evaluators import *
from .utils import Validators

# TODO: Use __name__ for the logger name instead of using the root logger
logger = logging.getLogger()


def get_evaluator_inputs_from_provider_inputs(provider_inputs, provider_module, input_data):
    # TODO: Get the inputs from given providers
    if provider_module == "terraform_plan":
        return terraform_provider(provider_inputs, input_data)
    elif provider_module == "infracost":
        return infracost_provider(provider_inputs, input_data)
    elif provider_module == "sg_workflow":
        return sg_wf_provider(provider_inputs, input_data)
    else:
        return []


def generate_evaluator_result(evaluator_obj, input_data, provider_module):

    eval_id = evaluator_obj.get("id")
    provider_inputs = evaluator_obj.get("provider_args")
    condition = evaluator_obj.get("condition")
    evaluator_class = None
    if condition:
        evaluator_class = condition.get("type")
        evaluator_data = condition.get("expected")
    else:
        print("condition key is not supplied.")

    evaluator_inputs = get_evaluator_inputs_from_provider_inputs(
        provider_inputs, provider_module, input_data
    )  # always an array of inputs for evaluators
    result = {
        "id": eval_id,
        "passed": False,
    }
    if evaluator_class:
        try:
            evaluator_instance = eval(f"{evaluator_class}()")
        except NameError:
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


def final_evaluator(eval_string, eval_id_values):
    logger.info("Running final evaluator")
    for key in eval_id_values:
        eval_string = eval_string.replace(key, str(eval_id_values[key]["passed"]))
        # print (eval_string)
    # TODO: shall we use and, or and not instead of symbols?
    eval_string = eval_string.replace(" ", "").replace("&&", " and ").replace("||", " or ").replace("!", " not ")
    return eval(eval_string)


# print(final_evaluator("(!(pol_check_1  &&  pol_check_2)  && pol_check_3 ) && pol_check_4", {
# 	"pol_check_1":False,
# 	"pol_check_2":True,
# 	"pol_check_3":True,
# 	"pol_check_4":False
# 	}))

# sg_policy --policy-path "F:\StackGuardian\policy-framework\tests\providers\policy.json" --input-path "F:\StackGuardian\policy-framework\tests\providers\input.json"


def start_policy_evaluation(policy_path, input_path):

    validator = Validators(policy_path)

    policy_data = validator.validate_policy()

    with open(input_path) as json_file:
        input_data = json.load(json_file)
    # TODO: validate input_data using the optionally available validate function in provider

    policy_meta = policy_data.get("meta")
    eval_objects = policy_data.get("evaluators")
    final_evaluation_policy_string = policy_data.get("eval_expression")
    provider_module = policy_meta.get("required_provider", "core")
    # TODO: Write functionality for dynamically importing evaluators from other modules.
    eval_results = []
    eval_results_obj = {}
    for eval_obj in eval_objects:
        eval_id = eval_obj.get("id")
        logger.info(f"Processing evaluator '{eval_id}'")
        eval_result = generate_evaluator_result(eval_obj, input_data, provider_module)
        eval_result["id"] = eval_id
        eval_results_obj[eval_id] = eval_result
        eval_results.append(eval_result)
    final_evaluation_result = final_evaluator(final_evaluation_policy_string, eval_results_obj)

    final_output = {
        "meta": {"version": policy_meta.get("version"), "required_provider": provider_module},
        "final_result": final_evaluation_result,
        "evaluators": eval_results,
    }
    return final_output
