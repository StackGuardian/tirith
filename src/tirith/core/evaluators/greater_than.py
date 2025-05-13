import logging
from typing import Dict, Any

from .base_evaluator import BaseEvaluator
from tirith.utils import json_format_value


logger = logging.getLogger(__name__)


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

# .. versionadded:: 1.0.0-alpha.1


class GreaterThan(BaseEvaluator):
    def evaluate(self, evaluator_input, evaluator_data):
        evaluation_result = {"passed": False, "message": "Not evaluated"}
        try:
            value1 = evaluator_input
            value2 = evaluator_data
            evaluation_result["passed"] = value1 > value2
            if evaluation_result["passed"]:
                evaluation_result["message"] = "{} is greater than {}".format(
                    json_format_value(value1), json_format_value(value2)
                )
            else:
                evaluation_result["message"] = "{} is not greater than {}".format(
                    json_format_value(value1), json_format_value(value2)
                )
            return evaluation_result
        except Exception as e:
            evaluation_result["message"] = str(e)
            return evaluation_result
