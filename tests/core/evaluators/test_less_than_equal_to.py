from sg_policy.core.evaluators import LessThanEqualTo
from pytest import mark

evaluator_input1 = 26
evaluator_data1 = 27

evaluator_input2 = 27
evaluator_data2 = 26

evaluator = LessThanEqualTo()

# pytest -v -m passing
@mark.passing
def test_evaluate_passing():
    result = evaluator.evaluate(evaluator_input1, evaluator_data1)
    assert result == {"passed": True, "message": f"{evaluator_input1} is less than equal to {evaluator_data1}"}


# pytest -v -m failing
@mark.passing
def test_evaluate_failing():
    result = evaluator.evaluate(evaluator_input2, evaluator_data2)
    assert result == {"passed": False, "message": f"{evaluator_input2} is not less than or equal to {evaluator_data2}"}
