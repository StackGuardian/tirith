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
    def evaluate(self, evaluator_input, evaluator_data):
        evaluation_result = {"passed": False, "message": "Not evaluated"}
        try:
            # if evaluator_input and evaluator_data are both strings
            if isinstance(evaluator_input, str) and isinstance(evaluator_data, str):
                result = evaluator_data in evaluator_input
                evaluation_result["passed"] = result
                if result:
                    evaluation_result["message"] = "Found {} inside {}".format(
                        json_format_value(evaluator_data), json_format_value(evaluator_input)
                    )
            # if evaluator_input is a list
            elif isinstance(evaluator_input, list):
                evaluator_input = sort_collections(evaluator_input)
                if isinstance(evaluator_data, list):
                    evaluator_data = sort_collections(evaluator_data)
                    result = evaluator_data in evaluator_input
                    evaluation_result["passed"] = result
                    if result:
                        evaluation_result["message"] = "Found {} inside {}".format(
                            json_format_value(evaluator_data), json_format_value(evaluator_input)
                        )
                    else:
                        evaluation_result["message"] = "Failed to find {} inside {}".format(
                            json_format_value(evaluator_data), json_format_value(evaluator_input)
                        )
                else:
                    result = evaluator_data in evaluator_input
                    evaluation_result["passed"] = result
                    if result:
                        evaluation_result["message"] = "Found {} inside {}".format(
                            json_format_value(evaluator_data), json_format_value(evaluator_input)
                        )
                    else:
                        evaluation_result["message"] = "Failed to find {} inside {}".format(
                            json_format_value(evaluator_data), json_format_value(evaluator_input)
                        )
            elif isinstance(evaluator_input, dict):
                if isinstance(evaluator_data, dict):
                    evaluation_result["passed"] = True
                    evaluation_result["message"] = "Found {} inside {}".format(
                        json_format_value(evaluator_data), json_format_value(evaluator_input)
                    )
                    for key in evaluator_data:
                        if key in evaluator_input:
                            if evaluator_input[key] != evaluator_data[key]:
                                evaluation_result["passed"] = False
                                evaluation_result["message"] = "Failed to find {} inside {}".format(
                                    json_format_value(evaluator_data), json_format_value(evaluator_input)
                                )
                                break
                        else:
                            evaluation_result["passed"] = False
                            evaluation_result["message"] = "Failed to find {} inside {}".format(
                                json_format_value(evaluator_data), json_format_value(evaluator_input)
                            )
                            break
                else:
                    result = evaluator_data in evaluator_input
                    evaluation_result["passed"] = result
                    if result:
                        evaluation_result["message"] = "Found {} inside {}".format(
                            json_format_value(evaluator_data), json_format_value(evaluator_input)
                        )
            else:
                evaluation_result["message"] = (
                    "{} is an unsupported data type for evaluating against value in 'condition.value'".format(
                        json_format_value(evaluator_data)
                    )
                )
            return evaluation_result
        except Exception as e:
            logger.exception(e)
            return evaluation_result
