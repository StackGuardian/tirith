from pytest import mark

from tirith.core.evaluators import LessThan

evaluator_input1 = 5
evaluator_data1 = 10

evaluator_input2 = 5
evaluator_data2 = 2

evaluator = LessThan()


# pytest -v -m passing
@mark.passing
def test_evaluate_passing():
    result = evaluator.evaluate(evaluator_input1, evaluator_data1)
    assert result == {"passed": True, "message": f"{evaluator_input1} is less than {evaluator_data1}"}


# pytest -v -m failing
@mark.failing
def test_evaluate_failing():
    result = evaluator.evaluate(evaluator_input2, evaluator_data2)
    assert result == {"passed": False, "message": f"{evaluator_input2} is not less than {evaluator_data2}"}
