from abc import ABC, abstractmethod
from typing import TypedDict


class EvaluatorResult(TypedDict):
    result: bool
    message: str
    error: str


class BaseEvaluator(ABC):

    # evaluate method will be called when the policy is evaluated using the policy evaluator
    @abstractmethod
    def evaluate(self) -> EvaluatorResult:
        return
