from typing import Dict, Type

from .base_evaluator import BaseEvaluator
from .contains import Contains
from .equals import Equals
from .greater_than_equal_to import GreaterThanEqualTo
from .greater_than import GreaterThan
from .is_empty import IsEmpty
from .is_not_empty import IsNotEmpty
from .less_than_equal_to import LessThanEqualTo
from .less_than import LessThan
from .regex_match import RegexMatch

EVALUATORS_DICT: Dict[str, Type[BaseEvaluator]] = {
    "Contains": Contains,
    "Equals": Equals,
    "GreaterThanEqualTo": GreaterThanEqualTo,
    "GreaterThan": GreaterThan,
    "IsEmpty": IsEmpty,
    "IsNotEmpty": IsNotEmpty,
    "LessThanEqualTo": LessThanEqualTo,
    "LessThan": LessThan,
    "RegexMatch": RegexMatch,
}
