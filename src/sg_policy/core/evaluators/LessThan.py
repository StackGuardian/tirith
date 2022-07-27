import BaseEvaluator

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
    def evaluate(self, evaluator_input, evaluator_data) -> bool:

        try:
            value1 = evaluator_input
            value2 = evaluator_data
            return value1 < value2
        except:
            return False
