from abc import ABC, abstractmethod
from typing import Any, Dict, TypedDict


class EvaluatorResult(TypedDict):
    passed: bool
    message: str
    error: str
    meta: Any


class BaseEvaluator(ABC):
    @abstractmethod
    def evaluate(self, evaluator_input: Dict, evaluator_data: Dict) -> EvaluatorResult:
        """
        This method will be called when the policy is evaluated using the policy evaluator
        """
        return
