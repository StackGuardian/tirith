from .base_evaluator import BaseEvaluator

# Checks if :attr:`value` is less then :attr:`other`. Automatically casts values to the same type if possible.

# Args:
#     value (mixed): Value to compare.
#     other (mixed): Other value to compare.

# Returns:
#     bool: Whether :attr:`value` is less then :attr:`other`.

# Example:

#     >>> l(None, None)
#     False
#     >>> l(2, 3)
#     True
#     >>> l('a', 'a')
#     False

# .. versionadded:: 1.0.0


class LessThan(BaseEvaluator):
    def evaluate(self, evaluator_input, evaluator_data):
        evaluation_result = {"passed": False, "message": "Failed before evaluation."}
        try:
            value1 = evaluator_input['value']
            value2 = evaluator_data
            evaluation_result["passed"] = value1 < value2
            if(value1 < value2):
                evaluation_result["message"] = "Evaluation passed successfully. Value {} is less than {}".format(
                    value1, value2
                )
            if not evaluation_result["passed"]:
                evaluation_result["message"] = "Value {} is not less than {}".format(
                    value1, value2
                )
            return evaluation_result
        except Exception as e:
            evaluation_result["message"] = str(e)
            return evaluation_result
