from sg_policy.core.evaluators import Equals
from pytest import mark

evaluator_input1 = {1, 2, 3, 4}
evaluator_data1 = {1, 2, 3, 4}

evaluator_input2 = {1, 2, 3, 4}
evaluator_data2 = {2, 3, 4}

evaluator = Equals()

# pytest -v -m passing
@mark.passing
def test_evaluate_passing():
    result = evaluator.evaluate(evaluator_input1, evaluator_data1)
    assert result == {"passed": True, "message": f"{evaluator_input1} is equal to {evaluator_data1}"}


# pytest -v -m failing
@mark.failing
def test_evaluate_failing():
    result = evaluator.evaluate(evaluator_input2, evaluator_data2)
    assert result == {"passed": False, "message": f"{evaluator_input2} is not equal to {evaluator_data2}"}
