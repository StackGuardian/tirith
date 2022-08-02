from base_evaluator import BaseEvaluator

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


class Equals(BaseEvaluator):
    def sort_lists_in_dicts(self, input):
        try:
            for key in input:
                if isinstance(input[key], list):
                    if isinstance(input[key][0], dict):
                        sorted_array = []
                        for index, item in enumerate(input[key]):
                            sorted_array.append(
                                self.sort_lists_in_dicts(input[key][index])
                            )
                        input[key] = sorted_array
                    elif isinstance(input[key][0], list):
                        sorted_array = []
                        for index, item in enumerate(input[key]):
                            sorted_array.append(
                                self.sort_lists_in_dicts(input[key][index])
                            )
                        input[key] = sorted_array
                    else:
                        input[key] = sorted(input[key])
                if isinstance(input[key], dict):
                    self.sort_lists_in_dicts(input[key])
            return input
        except Exception as e:
            return input

    def evaluate(self, evaluator_input, evaluator_data):
        evaluation_result = {"result": False, "message": "Equals evaluator failed"}
        try:
            value1 = evaluator_input
            value2 = evaluator_data

            # if (
            #         isinstance(evaluator_input, str)
            #         or isinstance(evaluator_input, dict)
            #         or isinstance(evaluator_input, list)
            # ):
            #     value1 = evaluator_input
            # else:
            #     value1 = str(evaluator_data)
            # if (
            #         isinstance(evaluator_data, str)
            #         or isinstance(evaluator_data, dict)
            #         or isinstance(evaluator_data, list)
            # ):
            #     value2 = evaluator_data
            # else:
            #     value2 = str(evaluator_data)

            evaluation_result["result"] = value1 == value2
            return evaluation_result
        except Exception as e:
            evaluation_result["message"] = str(e)
            return evaluation_result