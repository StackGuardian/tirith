from .base_evaluator import BaseEvaluator

# Checks if :attr:`value` is less then or equal to :attr:`other`. Automatically casts values to the same type if possible.

# Args:
#     value (mixed): Value to compare.
#     other (mixed): Other value to compare.

# Returns:
#     bool: Whether :attr:`value` is less then equal to :attr:`other`.

# Example:

#     >>> eq(None, None)
#     True
#     >>> eq(None, '')
#     False
#     >>> eq('a', 'a')
#     True
#     >>> eq(1, str(1))
#     False

# .. versionadded:: 1.0.0


class LessThanEqualTo(BaseEvaluator):
    def evaluate(self, evaluator_input, evaluator_data):
        evaluation_result = {
            "passed": False,
            "message": "Failed before evaluation.",
        }
        try:
            value1 = evaluator_input['value']
            value2 = evaluator_data
            evaluation_result["passed"] = value1 <= value2
            if(value1 <= value2):
                evaluation_result["message"] = "The evaluation passed successfully"
            if not evaluation_result["passed"]:
                evaluation_result[
                    "message"
                ] = "Value {} is not less than or equal to {}".format(value1, value2)
            return evaluation_result
        except Exception as e:
            evaluation_result["message"] = str(e)
            return evaluation_result
