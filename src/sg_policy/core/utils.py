import json


class Validators:
    # returns {"valid": bool, "message":str }
    # input
    def policy_validator(self, policy_input):
        # check if policy_input is valid JSON
        try:
            json.dumps(policy_input)
        except (TypeError, OverflowError):
            return {"valid": False, "message": "Policy is not a valid JSON"}
        # eval_objects = policy_data.get("evaluators")
        # check meta
        if "meta" not in policy_input or isinstance(policy_input["meta"], dict):
            return {"valid": False, "message": "Policy does not have a valid meta included"}
        elif "version" not in policy_input["meta"]:
            return {"valid": False, "message": "Policy does not have a version included in meta"}
        elif "required_provider" not in policy_input["meta"]:
            return {"valid": False, "message": "Policy does not have a required_provider included in meta"}
        # TODO: Verify the required_provider value

        if "evaluators" not in policy_input or isinstance(policy_input["evaluators"], list):
            return {"valid": False, "message": "Policy does not have a valid list of evaluators"}
        for evaluator in policy_input["evaluators"]:
            validation_result = self.evaluator_validator(evaluator)
            if not validation_result["valid"]:
                return {"valid": False, "message": validation_result["message"]}

        if "eval_expression" not in policy_input or isinstance(policy_input["eval_expression"], str):
            return {"valid": False, "message": "Policy does not have a valid eval_expression"}

        return {"valid": True, "message": "Policy Validated Successfully"}

    def evaluator_validator(self, evaluator):
        if not evaluator or isinstance(evaluator, dict):
            return {"valid": False, "message": "Invalid Evaluator provided"}
        if "id" not in evaluator:
            return {"valid": False, "message": "No id provided for evaluator"}
        eval_id = evaluator["id"]

        if "provider_args" not in evaluator or isinstance(evaluator["provider_args"], dict):
            return {"valid": False, "message": f"Invalid provider args for evaluator with evaluator id: {eval_id}"}

        if "condition" not in evaluator or isinstance(evaluator["condition"], dict):
            return {"valid": False, "message": f"Invalid conditon for evaluator with evaluator id: {eval_id}"}
        elif "type" not in evaluator["condition"] or isinstance(evaluator["condition"]["type"], str):
            return {"valid": False, "message": f"Invalid conditon type for evaluator with evaluator id: {eval_id}"}
