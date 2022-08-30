import less_than_equal_to as ltet
import pytest

evaluator_input1 = {"value": 26}
evaluator_data1 = 27

evaluator_input2 = {"value": 27}
evaluator_data2 = 26

a = ltet.LessThanEqualTo()

# pytest -v -m passing
@pytest.mark.passing
def test_evaluate_passing():
    result = a.evaluate(evaluator_input1, evaluator_data1)
    assert result == {"passed": True, "message": "The evaluation passed successfully"}


# pytest -v -m failing
@pytest.mark.passing
def test_evaluate_failing():
    result = a.evaluate(evaluator_input2, evaluator_data2)
    assert result == {"passed": True, "message": "The evaluation passed successfully"}
