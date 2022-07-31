import BaseEvaluator
import re

class regexEquals(BaseEvaluator.BaseEvaluator):
    def evaluate(self, evaluator_input, evaluator_data) -> bool:
        match = 0
        if (type(evaluator_input) == str and type(evaluator_data) == str):
            match = re.match(evaluator_data, evaluator_input)
            if match is None:
                return False
            else:
                return True
        return False
