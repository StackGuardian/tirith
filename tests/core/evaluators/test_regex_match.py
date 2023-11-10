from tirith.core.evaluators import RegexMatch
from pytest import mark

evaluator_data1 = "^(?=[a-zA-Z0-9._]{8,20}$)(?!.*[_.]{2})[^_.].*[^_.]$"
evaluator_input1 = "amitrakshar01"

evaluator_data2 = "^(?=[a-zA-Z0-9._]{8,20}$)(?!.*[_.]{2})[^_.].*[^_.]$"
evaluator_input2 = "@01amitrakshar"

evaluator = RegexMatch()


# pytest -v -m passing
@mark.passing
def test_regex_passing():
    result = evaluator.evaluate(evaluator_input1, evaluator_data1)
    assert result == {"passed": True, "message": f"{evaluator_input1} matches regex pattern {evaluator_data1}"}


# pytest -v -m failing
@mark.failing
def test_regex_failing():
    result = evaluator.evaluate(evaluator_input2, evaluator_data2)
    assert result == {"passed": False, "message": f"{evaluator_input2} does not match regex pattern {evaluator_data2}"}


def test_regex_list():
    result = evaluator.evaluate(evaluator_input=["something"], evaluator_data=r"\['something'\]")
    assert result["passed"] is True


def test_regex_dict():
    result = evaluator.evaluate(evaluator_input=dict(a=2), evaluator_data=r"{'a': 2}")
    assert result["passed"] is True
