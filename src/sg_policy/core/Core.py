from evaluators import *
import json


def getEvaluatorInputsFromProviderInputs(provider_inputs, evaluator_module):
    # TODO: Get the inputs from given providers
    if evaluator_module == "terraform_plan":

        return True


def generate_evaluator_result(evaluator_obj):
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
    providor_inputs = evaluator_obj.get("provider_inputs")
    evaluator_data = evaluator_obj.get("evaluator_data")

    evaluator_inputs = getEvaluatorInputsFromProviderInputs(
        providor_inputs, evaluator_module
    )
    if evaluator_module == "core":
        if evaluator_class == "Equals":
            evaluator_instance = Equals()
            result = evaluator_instance.evaluate(evaluator_inputs, evaluator_data)
            return result
        elif evaluator_class == "Contains":
            evaluator_instance = Contains()
            result = evaluator_instance.evaluate(evaluator_inputs, evaluator_data)
            return result


def finalEvaluator(evalString, evalIdValues):
    for key in evalIdValues:
        evalString = evalString.replace(key, str(evalIdValues[key]))
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


def start_policy_evaluation(policy_path, input_path):
    # TODO:
    with open(f"{policy_path}") as f:
        json_to_python = json.load(f)
        policy = json_to_python

    with open(f"{input_path}") as f:
        json_to_python = json.load(f)
        input_data = json_to_python

    policy_meta = policy.get("meta")
    eval_objects = policy.get("evaluators")
    final_evaluation_policy_string = policy.get("final_evaluation")

    # TODO: Write functionality for dynamically importing evaluators from other modules.
    eval_results = {}
    for eval_obj in eval_objects:
        eval_id = eval_obj.get("id")
        eval_results[eval_id] = generate_evaluator_result(eval_obj)

    final_evaluation_result = finalEvaluator(
        final_evaluation_policy_string, eval_results
    )
    print(final_evaluation_result)
