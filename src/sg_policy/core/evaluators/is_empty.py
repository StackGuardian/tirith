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

# .. versionadded:: 1.0.0


class IsEmpty(BaseEvaluator):
    def evaluate(self, input):
        evaluation_result = {"result": False, "message": ""}
        try:
            if (
                isinstance(input, str)
                or isinstance(input, list)
                or isinstance(input, dict)
            ) and not input:
                evaluation_result["result"] = True
            if not evaluation_result["result"]:
                evaluation_result["message"] = "Value {} is not empty".format(input)
            return evaluation_result
        except Exception as e:
            evaluation_result["message"] = str(e)
            return evaluation_result
