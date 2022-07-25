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
        if isinstance(input, str) and len(input) != 0:
            return True
        if isinstance(input, list) and len(input) != 0:
            return True
        if isinstance(input, dict) and len(input.keys()) != 0:
            return True
        return False
