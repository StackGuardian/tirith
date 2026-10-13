from .base_evaluator import BaseEvaluator


class EndsWith(BaseEvaluator):
    def evaluate(self, evaluator_input, evaluator_data):
        if not isinstance(evaluator_input, str):
            return {
                "passed": False,
                "message": "Expected input to be a string, got {}".format(type(evaluator_input).__name__),
            }

        passed = evaluator_input.endswith(evaluator_data)
        message = ("{} ends with {}" if passed else "{} does not end with {}").format(evaluator_input, evaluator_data)
        return {"passed": passed, "message": message}
