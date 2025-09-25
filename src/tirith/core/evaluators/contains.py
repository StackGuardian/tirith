import logging

from .base_evaluator import BaseEvaluator
from tirith.utils import sort_collections, json_format_value


logger = logging.getLogger(__name__)

# Checks if :attr: `evaluator_input` is contained in :attr:`evaluator_data`.

# Args:
#     value (mixed): Value to compare.
#     other (mixed): Other value to compare.

# Returns:
#     bool: Whether :attr:`value` contains :attr:`other`.

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


class Contains(BaseEvaluator):
    def _format_message(self, found, evaluator_data, evaluator_input):
        """Helper method to format evaluation messages consistently."""
        action = "Found" if found else "Failed to find"
        return "{} {} inside {}".format(action, json_format_value(evaluator_data), json_format_value(evaluator_input))

    def evaluate(self, evaluator_input, evaluator_data):
        evaluation_result = {"passed": False, "message": "Not evaluated"}
        try:
            # if evaluator_input and evaluator_data are both strings
            if isinstance(evaluator_input, str) and isinstance(evaluator_data, str):
                result = evaluator_data in evaluator_input
                evaluation_result["passed"] = result
                evaluation_result["message"] = self._format_message(result, evaluator_data, evaluator_input)

            # if evaluator_input is a list
            elif isinstance(evaluator_input, list):
                evaluator_input = sort_collections(evaluator_input)
                if isinstance(evaluator_data, list):
                    evaluator_data = sort_collections(evaluator_data)
                    result = evaluator_data in evaluator_input
                else:
                    result = evaluator_data in evaluator_input

                evaluation_result["passed"] = result
                evaluation_result["message"] = self._format_message(result, evaluator_data, evaluator_input)

            # if evaluator_input is a dict
            elif isinstance(evaluator_input, dict):
                if isinstance(evaluator_data, dict):
                    # Check if all key-value pairs in evaluator_data exist in evaluator_input
                    result = True
                    for key in evaluator_data:
                        if key not in evaluator_input or evaluator_input[key] != evaluator_data[key]:
                            result = False
                            break
                    evaluation_result["passed"] = result
                    evaluation_result["message"] = self._format_message(result, evaluator_data, evaluator_input)
                else:
                    # Check if evaluator_data is a key in evaluator_input dict
                    result = evaluator_data in evaluator_input
                    evaluation_result["passed"] = result
                    evaluation_result["message"] = self._format_message(result, evaluator_data, evaluator_input)

            else:
                evaluation_result["message"] = (
                    "{} is an unsupported data type for evaluating against value in 'condition.value'".format(
                        json_format_value(evaluator_input)
                    )
                )

            return evaluation_result
        except Exception as e:
            logger.exception(e)
            return evaluation_result
