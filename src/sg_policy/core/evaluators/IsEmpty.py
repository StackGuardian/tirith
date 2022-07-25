import BaseEvaluator

# Checks if input is empty

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
    def evaluate(self, input) -> bool:
        if (isinstance(input, str) or isinstance(input, list) or isinstance(input, dict)) and not input:
            return True
        return False
