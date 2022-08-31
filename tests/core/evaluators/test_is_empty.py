from sg_policy.core.evaluators import IsEmpty
from pytest import mark

evaluator_input1 = ""
evaluator_input2 = "stackguardian"

evaluator = IsEmpty()

# pytest -v -m passing
@mark.passing
def test_evaluate_passing():
    result = evaluator.evaluate(evaluator_input1)
    assert result == {"message": f"{evaluator_input1} is empty", "passed": True}


# pytest -v -m failing
@mark.failing
def test_evaluate_failing():
    result = evaluator.evaluate(evaluator_input1)
    assert result == {"message": f"{evaluator_input1} is not empty", "passed": False}

# pytest -v -m passing
@mark.passing
def test_evaluate_passing():
    result = evaluator.evaluate(evaluator_input2)
    assert result == {"message": f"{evaluator_input2} is empty", "passed": False}


# pytest -v -m failing
@mark.failing
def test_evaluate_failing():
    result = evaluator.evaluate(evaluator_input2)
    assert result == {"message": f"{evaluator_input2} is not empty", "passed": True}
