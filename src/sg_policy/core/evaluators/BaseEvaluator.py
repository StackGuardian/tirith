from abc import ABC, abstractmethod


class BaseEvaluator(ABC):

    # evaluate method will be called when the policy is evaluated using the policy evaluator
    @abstractmethod
    def evaluate(self) -> bool:
        return
