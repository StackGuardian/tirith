import is_not_empty as notempty
import pytest

evaluator_input1 = 'abc'
evaluator_input2 = ''

a = notempty.IsNotEmpty()

#pytest -v -m passing
@pytest.mark.passing
def test_evaluate_passing():
	result = a.evaluate(evaluator_input1) 
	assert result == {"passed": True, "message": "The evaluation passed successfully"}
 
#pytest -v -m failing
@pytest.mark.failing
def test_evaluate_failing():
	result = a.evaluate(evaluator_input2) 
	assert result == {"passed": True, "message": "The evaluation passed successfully"}