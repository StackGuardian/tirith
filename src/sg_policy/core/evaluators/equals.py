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
    def sort_collections(self, input):
        try:
            if isinstance(input, str) or isinstance(input, float) or isinstance(input, int) or isinstance(input, bool):
                return input
            elif isinstance(input, list):
                if (
                    isinstance(input[0], str)
                    or isinstance(input[0], float)
                    or isinstance(input[0], int)
                    or isinstance(input[0], bool)
                ):
                    input = sorted(input)
                    return input
                else:
                    sorted_list = []
                    for index, val in enumerate(input):
                        sorted_list.append(self.sort_collections(val))
                    return sorted_list
            elif isinstance(input, dict):
                sorted_dict = {}
                for key in input:
                    sorted_val = self.sort_collections(input[key])
                    sorted_dict[key] = sorted_val
                return sorted_dict
            else:
                return input
        except Exception as e:
            # TODO: LOG
            logger.exception(e)
            return input

    def sort_lists_in_dicts(self, input):
        if isinstance(input, str) or isinstance(input, float) or isinstance(input, int):
            return input
        try:
            for _, key in enumerate(input):
                if isinstance(input[key], list):
                    if isinstance(input[key][0], dict) or isinstance(input[key][0], list):
                        sorted_array = []
                        for index, _ in enumerate(input[key]):
                            sorted_array.append(self.sort_lists_in_dicts(input[key][index]))
                        input[key] = sorted_array
                    else:
                        input[key] = sorted(input[key])
                elif isinstance(input[key], dict):
                    input[key] = self.sort_lists_in_dicts(input[key])
                else:
                    input = sorted(input)
            return input
        except Exception as e:
            logger.exception(str(e))
            return input

    def evaluate(self, evaluator_input, evaluator_data):
        evaluation_result = {"passed": False, "message": "Not evaluated"}
        try:
            value1 = evaluator_input
            value2 = evaluator_data
            if isinstance(value1, dict) or isinstance(value1, list):
                value1 = self.sort_collections(value1)
            if isinstance(value2, dict) or isinstance(value2, list):
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
