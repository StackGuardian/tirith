import greater_than as greater
import pytest

evaluator_input1 = {'value': 5}
evaluator_data1 = 2

evaluator_input2 = {'value': 5}
evaluator_data2 = 9

a = greater.GreaterThan()

#pytest -v -m passing
@pytest.mark.passing
def test_evaluate_passing():
	result = a.evaluate(evaluator_input1, evaluator_data1) 
	assert result == {"passed": True, "message": ""}

#pytest -v -m failing
@pytest.mark.failing
def test_evaluate_failing():
	result = a.evaluate(evaluator_input2, evaluator_data2) 
	assert result == {"passed": True, "message": ""}
