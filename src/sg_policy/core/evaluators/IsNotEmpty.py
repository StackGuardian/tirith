import BaseEvaluator

# Checks if input is not empty

# Args:
#     value (mixed): Value to check.

# Returns:
#     bool: Whether :attr:`value` is not empty

# Example:

#     >>> e('')
#     False
#     >>> e("abc")
#     True
#     >>> l([])
#     False

# .. versionadded:: 1.0.0


class IsNotEmpty(BaseEvaluator):
    def evaluate(self, input) -> bool:
        if (isinstance(input, str) or isinstance(input, list) or isinstance(input, dict)) and input:
            return True
        return False
