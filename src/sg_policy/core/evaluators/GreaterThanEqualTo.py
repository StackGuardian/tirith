import BaseEvaluator

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
    def evaluate(self, evaluator_input, evaluator_data) -> bool:

        try:
            value1 = evaluator_input
            value2 = evaluator_data
            return value1 >= value2
        except:
            return False
