from tirith.core.evaluators import GreaterThan
from pytest import mark

evaluator_input1 = 5
evaluator_data1 = 2

evaluator_input2 = 5
evaluator_data2 = 9

evaluator = GreaterThan()


# pytest -v -m passing
@mark.passing
def test_evaluate_passing():
    result = evaluator.evaluate(evaluator_input1, evaluator_data1)
    assert result == {"passed": True, "message": f"`{evaluator_input1}` is greater than `{evaluator_data1}`"}


# pytest -v -m failing
@mark.failing
def test_evaluate_failing():
    result = evaluator.evaluate(evaluator_input2, evaluator_data2)
    assert result == {"passed": False, "message": f"`{evaluator_input2}` is not greater than `{evaluator_data2}`"}
