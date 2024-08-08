import logging

from tirith.utils import sort_collections


logger = logging.getLogger(__name__)


# Checks if :attr: `evaluator_input` is contained in :attr:`evaluator_data`.

# Args:
#     value (mixed): Value to compare.
#     other (mixed): Other value to compare.

# Returns:
#     bool: Whether :attr:`value` is contained in :attr:`other`.

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


class ContainedIn(BaseEvaluator):
    def evaluate(self, evaluator_input, evaluator_data):
        evaluation_result = {"passed": False, "message": "Not evaluated"}
        try:
            # if evaluator_input and evaluator_data are both strings
            if isinstance(evaluator_input, str) and isinstance(evaluator_data, str):
                result = evaluator_input in evaluator_data
                evaluation_result["passed"] = result
                if result:
                    evaluation_result["message"] = "Found {} inside {}".format(evaluator_input, evaluator_data)
            # if evaluator_input is a list
            elif isinstance(evaluator_data, list):
                evaluator_data = sort_collections(evaluator_data)
                if isinstance(evaluator_input, list):
                    evaluator_input = sort_collections(evaluator_input)
                    result = evaluator_input in evaluator_data
                    evaluation_result["passed"] = result
                    if result:
                        evaluation_result["message"] = "Found {} inside {}".format(evaluator_input, evaluator_data)
                    else:
                        evaluation_result["message"] = "Failed to find {} inside {}".format(
                            evaluator_input, evaluator_data
                        )
                else:
                    result = evaluator_input in evaluator_data
                    evaluation_result["passed"] = result
                    if result:
                        evaluation_result["message"] = "Found {} inside {}".format(evaluator_input, evaluator_data)
                    else:
                        evaluation_result["message"] = "Failed to find {} inside {}".format(
                            evaluator_input, evaluator_data
                        )
            elif isinstance(evaluator_data, dict):
                if isinstance(evaluator_input, dict):
                    evaluation_result["passed"] = True
                    evaluation_result["message"] = "Found {} inside {}".format(evaluator_input, evaluator_data)
                    for key in evaluator_input:
                        if key in evaluator_data:
                            if evaluator_data[key] != evaluator_input[key]:
                                evaluation_result["passed"] = False
                                evaluation_result["message"] = "Failed to find {} inside {}".format(
                                    evaluator_input, evaluator_data
                                )
                                break
                        else:
                            evaluation_result["passed"] = False
                            evaluation_result["message"] = "Failed to find {} inside {}".format(
                                evaluator_input, evaluator_data
                            )
                            break
                else:
                    result = evaluator_input in evaluator_data
                    evaluation_result["passed"] = result
                    if result:
                        evaluation_result["message"] = "Found {} inside {}".format(evaluator_input, evaluator_data)
            else:
                evaluation_result["message"] = (
                    "{} is an unsupported data type for evaluating against value in 'condition.value'".format(
                        evaluator_data
                    )
                )
            return evaluation_result
        except Exception as e:
            logger.exception(e)
            return evaluation_result
