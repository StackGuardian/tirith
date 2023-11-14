from .base_evaluator import BaseEvaluator
import re


class RegexMatch(BaseEvaluator):
    def evaluate(self, evaluator_input, evaluator_data):
        evaluation_result = {"passed": False, "message": "Not evaluated"}
        try:
            match = 0
            if type(evaluator_input) in (str, list, dict) and type(evaluator_data) == str:
                evaluator_input = str(evaluator_input)
                match = re.search(evaluator_data, evaluator_input)
                if match is None:
                    evaluation_result = {
                        "passed": False,
                        "message": "{} does not match regex pattern {}".format(evaluator_input, evaluator_data),
                    }
                else:
                    evaluation_result = {
                        "passed": True,
                        "message": "{} matches regex pattern {}".format(evaluator_input, evaluator_data),
                    }
            else:
                evaluation_result = {
                    "passed": False,
                    "message": "{} does not match regex pattern {}".format(evaluator_input, evaluator_data),
                }
            return evaluation_result
        except Exception as e:
            evaluation_result["message"] = str(e)
            return evaluation_result
