import BaseEvaluator


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
    def evaluate(self, evaluator_input, evaluator_data) -> bool:
        try:
            value1 = evaluator_input
            value2 = evaluator_data
            return value1 > value2
        except:
            return False
