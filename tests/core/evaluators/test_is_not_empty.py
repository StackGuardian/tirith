from pytest import mark

from tirith.core.evaluators import IsNotEmpty

evaluator_input1 = "abc"
evaluator_input2 = ""

evaluator = IsNotEmpty()


# pytest -v -m passing
@mark.passing
def test_evaluate_passing():
    result = evaluator.evaluate(evaluator_input1)
    assert result == {"passed": True, "message": f"{evaluator_input1} is not empty"}


# pytest -v -m passing
@mark.failing
def test_evaluate_passing():
    result = evaluator.evaluate(evaluator_input2)
    assert result == {"passed": False, "message": f"{evaluator_input2} is empty"}
