import contains as contains
import pytest

evaluator_data1= ['a', 'b', 'c', 'd']
evaluator_input1= 'a'

evaluator_data2= ['a', 'b', 'c', 'd']
evaluator_input2= 'e'

a = contains.Contains()

#pytest -v -m passing
@pytest.mark.passing
def test_evaluate_passing():
	result = a.evaluate(evaluator_input1, evaluator_data1) 
	assert result == {'message': '', 'passed': True}

#pytest -v -m failing
@pytest.mark.failing
def test_evaluate_failing():
	result = a.evaluate(evaluator_input2, evaluator_data2) 
	assert result == {'message': '', 'passed': True}