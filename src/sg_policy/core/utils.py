from genericpath import isfile
import simplejson as json
from jsonschema import validate
from jsonschema.exceptions import ValidationError
import os


POLICY_SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "policy_schema.json")

print("ddd: ", POLICY_SCHEMA_PATH)

OUTPUT_SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "output_schema.json")


class Validators:
    def __init__(self, policy_path):
        self.policy_path = policy_path
        self.schema_path = POLICY_SCHEMA_PATH

    def load_json_from_file(self, json_file):
        if os.path.isfile(json_file):
            try:
                with open(json_file, "r") as fp:
                    return json.load(fp)
            except ValueError as err:
                print(str(err))
                return False
        else:
            print(str("Not a file path."))
            return False

    def validate_policy(self):
        policy_json = self.load_json_from_file(self.policy_path)
        schema_json = self.load_json_from_file(self.schema_path)

        try:
            validate(instance=policy_json, schema=schema_json)
            return policy_json
        except ValidationError as err:
            print(str(err))
            raise

    def evaluator_validator(self, evaluator):
        if not evaluator or isinstance(evaluator, dict):
            return {"valid": False, "message": "Invalid Evaluator provided"}
        if "id" not in evaluator:
            return {"valid": False, "message": "No id provided for evaluator"}
        eval_id = evaluator["id"]

        if "provider_args" not in evaluator or isinstance(evaluator["provider_args"], dict):
            return {"valid": False, "message": f"Invalid provider args for evaluator with evaluator id: {eval_id}"}

        if "condition" not in evaluator or isinstance(evaluator["condition"], dict):
            return {"valid": False, "message": f"Invalid condition for evaluator with evaluator id: {eval_id}"}
        elif "type" not in evaluator["condition"] or isinstance(evaluator["condition"]["type"], str):
            return {"valid": False, "message": f"Invalid condition type for evaluator with evaluator id: {eval_id}"}
