from .base_evaluator import BaseEvaluator


# Checks if :attr:`value` is more then :attr:`other`. Automatically casts values to the same type if possible.

# Args:
#     value (mixed): Value to compare.
#     other (mixed): Other value to compare.

# Returns:
#     bool: Whether :attr:`value` is more then :attr:`other`.

# Example:

#     >>> m(None, None)
#     False
#     >>> m(3, 2)
#     True
#     >>> m('a', 'a')
#     False

# .. versionadded:: 1.0.0


class GreaterThan(BaseEvaluator):
    def evaluate(self, evaluator_input, evaluator_data):
        evaluation_result = {"passed": False, "message": ""}
        try:
            value1 = evaluator_input['value']
            value2 = evaluator_data
            evaluation_result["passed"] = value1 > value2
            if not evaluation_result["passed"]:
                evaluation_result["message"] = "Value {} is not greater than {}".format(
                    value1, value2
                )
            return evaluation_result
        except Exception as e:
            evaluation_result["message"] = str(e)
            return evaluation_result
