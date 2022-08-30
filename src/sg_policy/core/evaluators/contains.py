from .base_evaluator import BaseEvaluator

# Checks if :attr: `evaluator_input` is contained in :attr:`evaluator_data`.

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


class Contains(BaseEvaluator):
    def sort_lists_in_dicts(self, input):
        if isinstance(input, str) or isinstance(input, float) or isinstance(input, int):
            return input
        try:
            for key in input:
                if isinstance(input[key], list):
                    if isinstance(input[key][0], dict) or isinstance(input[key][0], list):
                        sorted_array = []
                        for index, _ in enumerate(input[key]):
                            sorted_array.append(self.sort_lists_in_dicts(input[key][index]))
                        input[key] = sorted_array
                    else:
                        input[key] = sorted(input[key])
                if isinstance(input[key], dict):
                    self.sort_lists_in_dicts(input[key])
            return input
        except Exception as e:
            # TODO: logging
            return input

    def evaluate(self, evaluator_input, evaluator_data):
        evaluation_result = {"passed": False, "message": "Not evaluated"}
        try:
            # if evaluator_input and evaluator_data are both strings
            if isinstance(evaluator_input, str) and isinstance(evaluator_data, str):
                evaluation_result["passed"] = evaluator_input in evaluator_data
            # if evaluator_input is a list
            if isinstance(evaluator_data, list):
                evaluator_data = self.sort_lists_in_dicts(evaluator_data)
                if isinstance(evaluator_input, list):
                    evaluator_input = self.sort_lists_in_dicts(evaluator_input)
                    evaluation_result["passed"] = evaluator_input in evaluator_data
                else:
                    evaluation_result["passed"] = evaluator_input in evaluator_data
            if isinstance(evaluator_data, dict):
                if isinstance(evaluator_input, dict):
                    for key in evaluator_data:
                        if key in evaluator_input:
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
                    evaluation_result["passed"] = evaluator_input in evaluator_data
                    if evaluator_input in evaluator_data:
                        evaluation_result["message"] = "Failed to find {} inside {}".format(
                            evaluator_input, evaluator_data
                        )
            if evaluation_result["passed"]:
                evaluation_result["message"] = "Found {} inside {}".format(evaluator_input, evaluator_data)
            return evaluation_result
        except Exception as e:
            # TODO: logging
            return evaluation_result
