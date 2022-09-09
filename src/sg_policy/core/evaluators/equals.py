import logging

from .base_evaluator import BaseEvaluator

# TODO: Use __name__ for the logger name instead of using the root logger
logger = logging.getLogger()

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

# .. versionadded:: 1.0.0-alpha.1


class Equals(BaseEvaluator):
    def sort_collections(self, evaluator_input):
        try:
            if isinstance(evaluator_input, (str, float, int, bool)):
                return evaluator_input
            elif isinstance(evaluator_input, list):
                if (
                    isinstance(evaluator_input[0], (str, float, int, bool))
                ):
                    evaluator_input = sorted(evaluator_input)
                    return evaluator_input
                else:
                    sorted_list = []
                    for index, val in enumerate(evaluator_input):
                        sorted_list.append(self.sort_collections(val))
                    return sorted_list
            elif isinstance(evaluator_input, dict):
                sorted_dict = {}
                for key in evaluator_input:
                    sorted_val = self.sort_collections(evaluator_input[key])
                    sorted_dict[key] = sorted_val
                return sorted_dict
            else:
                return evaluator_input
        except Exception as e:
            # TODO: LOG
            logger.exception(e)
            return evaluator_input

    def sort_lists_in_dicts(self, evaluator_input):
        if isinstance(evaluator_input, (str, float, int)):
            return evaluator_input
        try:
            for _, key in enumerate(evaluator_input):
                if isinstance(evaluator_input[key], list):
                    if isinstance(evaluator_input[key][0], (dict, list)):
                        sorted_array = []
                        for index, _ in enumerate(evaluator_input[key]):
                            sorted_array.append(self.sort_lists_in_dicts(evaluator_input[key][index]))
                        evaluator_input[key] = sorted_array
                    else:
                        evaluator_input[key] = sorted(evaluator_input[key])
                elif isinstance(evaluator_input[key], dict):
                    evaluator_input[key] = self.sort_lists_in_dicts(evaluator_input[key])
                else:
                    evaluator_input = sorted(evaluator_input)
            return evaluator_input
        except Exception as e:
            logger.exception(str(e))
            return evaluator_input

    def evaluate(self, evaluator_input, evaluator_data):
        evaluation_result = {"passed": False, "message": "Not evaluated"}
        try:
            value1 = evaluator_input
            value2 = evaluator_data
            if isinstance(value1, (dict, list)):
                value1 = self.sort_collections(value1)
            if isinstance(value2, (dict, list)):
                value2 = self.sort_collections(value2)
            result = value1 == value2
            evaluation_result["passed"] = result
            if result:
                evaluation_result["message"] = "{} is equal to {}".format(evaluator_input, evaluator_data)
            else:
                evaluation_result["message"] = "{} is not equal to {}".format(evaluator_input, evaluator_data)
            return evaluation_result
        except Exception as e:
            evaluation_result["message"] = str(e)
            return evaluation_result
