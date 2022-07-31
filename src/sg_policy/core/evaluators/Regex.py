import BaseEvaluator
import re

class regexEquals(BaseEvaluator.BaseEvaluator):
    def evaluate(self, evaluator_input, evaluator_data) -> bool:
        match = re.match(evaluator_data, evaluator_input)
        if match is None:
            return False
        else:
            return True