import BaseEvaluator

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
        evaluation_result = {"result": False, "reason": "IsEmpty evaluator failed"}
        try:
            if (isinstance(input, str) or isinstance(input, list) or isinstance(input, dict)) and not input:
                evaluation_result["result"] = True
            return evaluation_result
        except Exception as e:
            evaluation_result["reason"] = str(e)
            return evaluation_result
