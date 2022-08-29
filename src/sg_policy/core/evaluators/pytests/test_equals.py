import equals as equals
import pytest

evaluator_input1 = {1,2,3,4}
evaluator_data1 = {1,2,3,4}

evaluator_input2 = {1,2,3,4}
evaluator_data2 = {2,3,4}

a = equals.Equals()

#pytest -v -m passing
@pytest.mark.passing
def test_evaluate_passing():
	result = a.evaluate(evaluator_input1, evaluator_data1) 
	assert result == {"passed": True, "message": "The evaluation passed successfully"}

#pytest -v -m failing
@pytest.mark.failing
def test_evaluate_failing():
	result = a.evaluate(evaluator_input2, evaluator_data2) 
	assert result == {"passed": True, "message": "The evaluation passed successfully"}