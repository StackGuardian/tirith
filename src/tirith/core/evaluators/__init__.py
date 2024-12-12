from typing import Dict, Type

from .base_evaluator import BaseEvaluator
from .contained_in import ContainedIn
from .contains import Contains
from .equals import Equals
from .greater_than_equal_to import GreaterThanEqualTo
from .greater_than import GreaterThan
from .is_empty import IsEmpty
from .is_not_empty import IsNotEmpty
from .less_than_equal_to import LessThanEqualTo
from .less_than import LessThan
from .regex_match import RegexMatch
from .not_equals import NotEquals
from .not_contained_in import NotContainedIn
from .not_contains import NotContains
from .version_compare import VersionCompare

EVALUATORS_DICT: Dict[str, Type[BaseEvaluator]] = {
    "ContainedIn": ContainedIn,
    "Contains": Contains,
    "Equals": Equals,
    "GreaterThanEqualTo": GreaterThanEqualTo,
    "GreaterThan": GreaterThan,
    "IsEmpty": IsEmpty,
    "IsNotEmpty": IsNotEmpty,
    "LessThanEqualTo": LessThanEqualTo,
    "LessThan": LessThan,
    "RegexMatch": RegexMatch,
    "NotEquals": NotEquals,
    "NotContainedIn": NotContainedIn,
    "NotContains": NotContains,
    "VersionCompare": VersionCompare
}
