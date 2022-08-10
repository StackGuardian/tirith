from .evaluators import *
from pathlib import Path
import json
from ..providers.python.infracost import provide


def getEvaluatorInputsFromProviderInputs(provider_inputs, evaluator_module, input_data):
    # TODO: Get the inputs from given providers
    if evaluator_module == "terraform_plan":
        return [True]
    if evaluator_module == "infracost":
        return provide(provider_inputs, input_data)


def generate_evaluator_result(evaluator_obj, input_data):
    # evaluator_obj example
    # {
    #         "id": "pol_check_1",
    #         "provider": "terraform_plan", //which provider to import evaluator from (core by default)
    #         "provider_inputs": { // Use provider_data or evaluator_inputs
    #             "transformer_ref": "count",
    #             "resource_type": "aws_s3_bucket"
    #         },
    #         "evaluator_ref": "lt",
    #         "evaluator_data": 10, // Should also support transformation eventually
    #         "evaluator_inputs": 10
    #     },
    evaluator_module = evaluator_obj.get("provider", "core")
    evaluator_class = evaluator_obj.get("evaluator_ref")
    provider_inputs = evaluator_obj.get("provider_inputs")
    evaluator_data = evaluator_obj.get("evaluator_data")
    eval_id = evaluator_obj.get("id")

    # print({
    #     'evaluator_module' : evaluator_module,
    #     'evaluator_class': evaluator_class,
    #     'provider_inputs': provider_inputs,
    #     'evaluator_data': evaluator_data,
    #     'eval_id': eval_id
    # })

    evaluator_inputs = getEvaluatorInputsFromProviderInputs(
        provider_inputs, evaluator_module, input_data
    )  # always an array of inputs for evaluators
    if evaluator_module == "core":
        result = {
            "id": eval_id,
            "results": [],
            "passed": False,
        }
        try:
            evaluator_instance = eval(f"{evaluator_class}()")
        except NameError as e:
            print(f"{evaluator_class} is not a supported evaluator.")
        evaluation_results = []
        has_evaluation_passed = True
        for evaluator_input in evaluator_inputs:
            evaluation_result = evaluator_instance.evaluate(
                evaluator_input, evaluator_data
            )
            evaluation_results.append(evaluation_result)
            if not evaluation_result["passed"]:
                has_evaluation_passed = False
        result["result"] = evaluation_results
        result["passed"] = has_evaluation_passed
        return result

    if evaluator_module == "infracost":
        result = {
            "id": eval_id,
            "results": [],
            "passed": False,
        }
        try:
            evaluator_instance = eval(f"{evaluator_class}()")
        except NameError as e:
            print(f"{evaluator_class} is not a supported evaluator.")
        evaluation_results = []
        has_evaluation_passed = True
        for evaluator_input in evaluator_inputs:
            evaluation_result = evaluator_instance.evaluate(
                evaluator_input, evaluator_data
            )
            evaluation_results.append(evaluation_result)
            if not evaluation_result["result"]:
                has_evaluation_passed = False
        result["result"] = evaluation_results
        result["passed"] = has_evaluation_passed
        return result


def finalEvaluator(evalString, evalIdValues):
    for key in evalIdValues:
        evalString = evalString.replace(key, str(evalIdValues[key]["passed"]))
        # print (evalString)
    evalString = (
        evalString.replace(" ", "")
            .replace("&&", " and ")
            .replace("||", " or ")
            .replace("!", " not ")
    )
    return eval(evalString)


# print(finalEvaluator("(!(pol_check_1  &&  pol_check_2)  && pol_check_3 ) && pol_check_4", {
# 	"pol_check_1":False,
# 	"pol_check_2":True,
# 	"pol_check_3":True,
# 	"pol_check_4":False
# 	}))

# sg_policy --policy-path "F:\StackGuardian\policy-framework\tests\providers\policy.json" --input-path "F:\StackGuardian\policy-framework\tests\providers\input.json"

def start_policy_evaluation(policy_path, input_path):
    # policy_data = Path(policy_path).read_text()
    policy_data = json.load(open(policy_path))
    # TODO: validate policy_data against schema

    # input_data = Path(input_path).read_text()
    input_data = json.load(open(input_path))
    # TODO: validate input_data using the optionally available validate function in provider

    policy_meta = policy_data.get("meta")
    eval_objects = policy_data.get("evaluators")
    final_evaluation_policy_string = policy_data.get("final_evaluation")

    # TODO: Write functionality for dynamically importing evaluators from other modules.
    eval_results = {}
    for eval_obj in eval_objects:
        eval_id = eval_obj.get("id")
        eval_results[eval_id] = generate_evaluator_result(eval_obj, input_data)
    final_evaluation_result = finalEvaluator(
        final_evaluation_policy_string, eval_results
    )

    final_output = {
        "meta": {"version": "1.0.0"},
        "final_evaluation": final_evaluation_result,
        "evaluators": eval_results,
    }
    return final_output
