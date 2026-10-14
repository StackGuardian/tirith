from tirith.core.evaluators import IsNotEmpty
from pytest import mark
from tirith.utils import json_format_value

checks_passing = ("abc", " ", {"a": None})
checks_failing = ("", 0, False)

evaluator = IsNotEmpty()


# pytest -v -m passing
@mark.passing
@mark.parametrize("evaluator_input", checks_passing)
def test_evaluate_passing(evaluator_input):
    result = evaluator.evaluate(evaluator_input)
    assert result == {"passed": True, "message": f"{json_format_value(evaluator_input)} is not empty"}


# pytest -v -m failing
@mark.failing
@mark.parametrize("evaluator_input", checks_failing)
def test_evaluate_failing(evaluator_input):
    result = evaluator.evaluate(evaluator_input)
    assert result == {"passed": False, "message": f"{json_format_value(evaluator_input)} is empty"}
