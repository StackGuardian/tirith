import logging
from typing import Dict, Any

from .base_evaluator import BaseEvaluator
from tirith.utils import sort_collections, json_format_value

logger = logging.getLogger(__name__)

# Checks if :attr:`value` is not equal to :attr:`other`. Automatically casts values to the same type if possible.

# Args:
#     value (mixed): Value to compare.
#     other (mixed): Other value to compare.

# Returns:
#     bool: Whether :attr:`value` is not equal to :attr:`other`.

# Example:

#     >>> not_eq(None, None)
#     False
#     >>> not_eq(None, '')
#     True
#     >>> not_eq('a', 'a')
#     False
#     >>> not_eq(1, str(1))
#     True

# .. versionadded:: 1.0.0-alpha.1


class NotEquals(BaseEvaluator):
    def evaluate(self, evaluator_input, evaluator_data):
        evaluation_result = {"passed": False, "message": "Not evaluated"}
        try:
            value1 = evaluator_input
            value2 = evaluator_data
            if isinstance(value1, dict) or isinstance(value1, list):
                value1 = sort_collections(value1)
            if isinstance(value2, dict) or isinstance(value2, list):
                value2 = sort_collections(value2)
            result = value1 != value2
            evaluation_result["passed"] = result
            if result:
                evaluation_result["message"] = "{} is not equal to {}".format(
                    json_format_value(evaluator_input), json_format_value(evaluator_data)
                )
            else:
                evaluation_result["message"] = "{} is equal to {}".format(
                    json_format_value(evaluator_input), json_format_value(evaluator_data)
                )
            return evaluation_result
        except Exception as e:
            evaluation_result["message"] = str(e)
            return evaluation_result
