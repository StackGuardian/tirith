from base_evaluator import BaseEvaluator

# Checks if :attr:`value` is more then or equal to :attr:`other`. Automatically casts values to the same type if possible.

# Args:
#     value (mixed): Value to compare.
#     other (mixed): Other value to compare.

# Returns:
#     bool: Whether :attr:`value` is more then equal to :attr:`other`.

# Example:

#     >>> meq(None, None)
#     True
#     >>> meq(None, '')
#     False
#     >>> meq('a', 'a')
#     True
#     >>> meq(1, str(1))
#     False

# .. versionadded:: 1.0.0


class GreaterThanEqualTo(BaseEvaluator):
    def evaluate(self, evaluator_input, evaluator_data):
        evaluation_result = {"result": False, "message": "GreaterThanEqualTo evaluator failed"}
        try:
            value1 = evaluator_input
            value2 = evaluator_data
            evaluation_result["result"] = value1 >= value2
            return evaluation_result
        except Exception as e:
            evaluation_result["message"] = str(e)
            return evaluation_result
