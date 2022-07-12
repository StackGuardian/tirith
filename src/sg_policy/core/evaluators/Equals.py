import BaseEvaluator


class Equals(BaseEvaluator):
    def evaluate(value, other) -> bool:
        # Checks if :attr:`value` is equal to :attr:`other`. Automatically casts values to the same type if possible.

        # Args:
        #     value (mixed): Value to compare.
        #     other (mixed): Other value to compare.

        # Returns:
        #     bool: Whether :attr:`value` is equal to :attr:`other`.

        # Example:

        #     >>> eq(None, None)
        #     True
        #     >>> eq(None, '')
        #     False
        #     >>> eq('a', 'a')
        #     True
        #     >>> eq(1, str(1))
        #     False

        # .. versionadded:: 1.0.0
        value1 = value
        value2 = other
        if (
            isinstance(value, str)
            or isinstance(value, object)
            or isinstance(value, list)
        ):
            value1 = value
        else:
            value1 = str(value)
        if (
            isinstance(other, str)
            or isinstance(other, object)
            or isinstance(other, list)
        ):
            value2 = other
        else:
            value2 = str(other)

        return value1 == value2
