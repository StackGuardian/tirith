import json
import logging
import re

from typing import Dict
from ..providers import PROVIDERS_DICT
from .evaluators import EVALUATORS_DICT


# TODO: Use __name__ for the logger name instead of using the root logger
logger = logging.getLogger()


def get_evaluator_inputs_from_provider_inputs(provider_inputs, provider_module, input_data):
    # TODO: Get the inputs from given providers
    provider_func = PROVIDERS_DICT.get(provider_module)

    if provider_func is None:
        logger.error(f"Provider '{provider_module}' is not found")
        return []
    return provider_func(provider_inputs, input_data)


def generate_evaluator_result(evaluator_obj, input_data, provider_module):
    eval_id = evaluator_obj.get("id")
    provider_inputs = evaluator_obj.get("provider_args")
    condition = evaluator_obj.get("condition")
    evaluator_name: str = condition.get("type")
    evaluator_data = condition.get("expected")

    if not condition:
        logger.error("condition key is not supplied.")

    evaluator_inputs = get_evaluator_inputs_from_provider_inputs(
        provider_inputs, provider_module, input_data
    )  # always an array of inputs for evaluators

    result = {
        "id": eval_id,
        "passed": False,
    }
    evaluator_class = EVALUATORS_DICT.get(evaluator_name)
    if evaluator_class is None:
        logger.error(f"{evaluator_name} is not a supported evaluator")
        return result

    evaluator_instance = evaluator_class()
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


def final_evaluator(eval_string: str, eval_id_values: Dict[str, bool]) -> bool:
    """
    Evaluate a given boolean expression string `eval_string` based on the boolean
    values provided by `eval_id_values`.

    Example usage:
    >>> final_evaluator("(!(pol_check_1  &&  pol_check_2)  && pol_check_3 ) && pol_check_4", {
        "pol_check_1":False,
        "pol_check_2":True,
        "pol_check_3":True,
        "pol_check_4":False
    })
    """
    logger.debug("Running final evaluator")
    for key in eval_id_values:
        regex_string = "\\b" + key + "\\b"
        eval_string = re.sub(regex_string, str(eval_id_values[key]), eval_string)
        # eval_string = eval_string.replace(key, str(eval_id_values[key]["passed"]))
        # print (eval_string)

    # TODO: shall we use and, or and not instead of symbols?

    eval_string = eval_string.replace(" ", "").replace("&&", " and ").replace("||", " or ").replace("!", " not ")
    return eval(eval_string)


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
    eval_results = []
    eval_results_obj = {}
    for eval_obj in eval_objects:
        eval_id = eval_obj.get("id")
        logger.debug(f"Processing evaluator '{eval_id}'")
        eval_result = generate_evaluator_result(eval_obj, input_data, provider_module)
        eval_result["id"] = eval_id
        eval_results_obj[eval_id] = eval_result["passed"]
        eval_results.append(eval_result)
    final_evaluation_result = final_evaluator(final_evaluation_policy_string, eval_results_obj)

    final_output = {
        "meta": {"version": policy_meta.get("version"), "required_provider": provider_module},
        "final_result": final_evaluation_result,
        "evaluators": eval_results,
    }
    return final_output
