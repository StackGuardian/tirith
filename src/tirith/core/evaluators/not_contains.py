import logging

from .base_evaluator import BaseEvaluator
from tirith.utils import sort_collections


logger = logging.getLogger(__name__)

# Checks if :attr: `evaluator_input` does not contain :attr:`evaluator_data`.

# Args:
#     value (mixed): Value to compare.
#     other (mixed): Other value to compare.

# Returns:
#     bool: Whether :attr:`value` does not contain :attr:`other`.

# Example:

#     >>> eq(None, None)
#     False
#     >>> eq(None, '')
#     True
#     >>> eq('a', 'a')
#     False
#     >>> eq(1, str(1))
#     True

# .. versionadded:: 1.0.0-beta.12


class NotContains(BaseEvaluator):
    def evaluate(self, evaluator_input, evaluator_data):
        evaluation_result = {"passed": False, "message": "Not evaluated"}
        try:
            # if evaluator_input and evaluator_data are both strings
            if isinstance(evaluator_input, str) and isinstance(evaluator_data, str):
                result = evaluator_data not in evaluator_input
                evaluation_result["passed"] = result
                if result:
                    evaluation_result["message"] = "Did not find {} inside {}".format(evaluator_data, evaluator_input)
                else:
                    evaluation_result["message"] = "Found {} inside {}".format(evaluator_data, evaluator_input)
            # if evaluator_input is a list
            elif isinstance(evaluator_input, list):
                evaluator_input = sort_collections(evaluator_input)
                if isinstance(evaluator_data, list):
                    evaluator_data = sort_collections(evaluator_data)
                    result = evaluator_data not in evaluator_input
                    evaluation_result["passed"] = result
                    if result:
                        evaluation_result["message"] = "Did not find {} inside {}".format(
                            evaluator_data, evaluator_input
                        )
                    else:
                        evaluation_result["message"] = "Found {} inside {}".format(evaluator_data, evaluator_input)
                else:
                    result = evaluator_data not in evaluator_input
                    evaluation_result["passed"] = result
                    if result:
                        evaluation_result["message"] = "Did not find {} inside {}".format(
                            evaluator_data, evaluator_input
                        )
                    else:
                        evaluation_result["message"] = "Found {} inside {}".format(evaluator_data, evaluator_input)
            elif isinstance(evaluator_input, dict):
                if isinstance(evaluator_data, dict):
                    evaluation_result["passed"] = True
                    evaluation_result["message"] = "Did not find {} inside {}".format(evaluator_data, evaluator_input)
                    for key in evaluator_data:
                        if key not in evaluator_input:
                            continue

                        if evaluator_input[key] == evaluator_data[key]:  # changes for xontains
                            evaluation_result["passed"] = False
                            evaluation_result["message"] = "Found {} inside {}".format(evaluator_data, evaluator_input)
                            break
                else:
                    result = evaluator_data not in evaluator_input
                    evaluation_result["passed"] = result
                    if result:
                        evaluation_result["message"] = "Did not find {} inside {}".format(
                            evaluator_data, evaluator_input
                        )
                    else:
                        evaluation_result["message"] = "Found {} inside {}".format(evaluator_data, evaluator_input)

            else:
                evaluation_result["passed"] = False
                evaluation_result["message"] = (
                    "{} is an unsupported data type for evaluating against value in 'condition.value'".format(
                        evaluator_data
                    )
                )
            return evaluation_result
        except Exception as e:
            logger.exception(e)
            return evaluation_result
