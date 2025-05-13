import logging
from typing import Dict, Any

from .base_evaluator import BaseEvaluator
from tirith.utils import json_format_value

# Checks if :attr:`value` is less then or equal to :attr:`other`. Automatically casts values to the same type if possible.

# Args:
#     value (mixed): Value to compare.
#     other (mixed): Other value to compare.

# Returns:
#     bool: Whether :attr:`value` is less then equal to :attr:`other`.

# Example:

#     >>> eq(None, None)
#     True
#     >>> eq(None, '')
#     False
#     >>> eq('a', 'a')
#     True
#     >>> eq(1, str(1))
#     False

# .. versionadded:: 1.0.0-alpha.1


class LessThanEqualTo(BaseEvaluator):
    def evaluate(self, evaluator_input, evaluator_data):
        evaluation_result = {
            "passed": False,
            "message": "Not evaluated",
        }
        try:
            value1 = evaluator_input
            value2 = evaluator_data
            evaluation_result["passed"] = value1 <= value2
            if evaluation_result["passed"]:
                evaluation_result["message"] = "{} is less than equal to {}".format(
                    json_format_value(value1), json_format_value(value2)
                )
            else:
                evaluation_result["message"] = "{} is not less than or equal to {}".format(
                    json_format_value(value1), json_format_value(value2)
                )
            return evaluation_result
        except Exception as e:
            evaluation_result["message"] = str(e)
            return evaluation_result
