from .base_evaluator import BaseEvaluator

# Checks if input is empty (null, empty list [], empty dict {}, empty str '')

# Args:
#     value (mixed): Value to check.

# Returns:
#     bool: Whether :attr:`value` is empty

# Example:

#     >>> e('')
#     True
#     >>> e("abc")
#     False
#     >>> l([])
#     True

# .. versionadded:: 1.0.0-alpha.1


class IsEmpty(BaseEvaluator):
    def evaluate(self, input):
        evaluation_result = {"passed": False, "message": "Failed before evaluation."}
        try:
            if (
                isinstance(input, str)
                or isinstance(input, list)
                or isinstance(input, dict)
            ) and not input:
                evaluation_result["passed"] = True
                evaluation_result["message"] = "Value {} is empty".format(
                    input
                )
            if not evaluation_result["passed"]:
                evaluation_result["message"] = "Value {} is not empty".format(input)
            return evaluation_result
        except Exception as e:
            evaluation_result["message"] = str(e)
            return evaluation_result
