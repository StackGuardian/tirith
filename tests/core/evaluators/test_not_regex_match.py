from tirith.core.evaluators import NotRegexMatch
from pytest import mark
from tirith.utils import json_format_value

evaluator_data1 = "^(?=[a-zA-Z0-9._]{8,20}$)(?!.*[_.]{2})[^_.].*[^_.]$"
evaluator_input1 = "amitrakshar01"

evaluator_data2 = "^(?=[a-zA-Z0-9._]{8,20}$)(?!.*[_.]{2})[^_.].*[^_.]$"
evaluator_input2 = "@01amitrakshar"

evaluator = NotRegexMatch()


# pytest -v -m passing
@mark.passing
def test_not_regex_passing():
    result = evaluator.evaluate(evaluator_input2, evaluator_data2)
    assert result == {
        "passed": True,
        "message": f"{json_format_value(evaluator_input2)} does not match regex pattern {json_format_value(evaluator_data2)}",
    }


# pytest -v -m failing
@mark.failing
def test_not_regex_failing():
    result = evaluator.evaluate(evaluator_input1, evaluator_data1)
    assert result == {
        "passed": False,
        "message": f"{json_format_value(evaluator_input1)} matches regex pattern {json_format_value(evaluator_data1)}",
    }


def test_not_regex_list():
    result = evaluator.evaluate(evaluator_input=["something"], evaluator_data=r"\['other'\]")
    assert result["passed"] is True
    result_fail = evaluator.evaluate(evaluator_input=["something"], evaluator_data=r"\['something'\]")
    assert result_fail["passed"] is False


def test_not_regex_dict():
    result = evaluator.evaluate(evaluator_input=dict(a=2), evaluator_data=r"{'b': 1}")
    assert result["passed"] is True
    result_fail = evaluator.evaluate(evaluator_input=dict(a=2), evaluator_data=r"{'a': 2}")
    assert result_fail["passed"] is False


def test_not_regex_invalid_pattern():
    result = evaluator.evaluate(evaluator_input="something", evaluator_data="[invalid_regex")
    assert result["passed"] is False
    assert "unterminated character set" in result["message"]
