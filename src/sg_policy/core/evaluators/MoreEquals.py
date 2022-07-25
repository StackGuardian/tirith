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


class MoreEquals(BaseEvaluator):
    def evaluate(self, evaluator_input, evaluator_data) -> bool:

        value1 = evaluator_input
        value2 = evaluator_data

        # Currently supporting int, float and string
        if (
            isinstance(evaluator_input, str)
            or isinstance(evaluator_input, int)
            or isinstance(evaluator_input, float)
        ) and (
            isinstance(evaluator_data, str)
            or isinstance(evaluator_data, int)
            or isinstance(evaluator_data, float)
        ):
            value1 = str(evaluator_input)
            value2 = str(evaluator_data)

            return value1 >= value2
        else:
            return False
