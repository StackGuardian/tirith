import contains as contains

evaluator_data= ['a', 'b', 'c', 'd']
evaluator_input= 'a'

a = contains.Contains()

def test_evaluate():
	result = a.evaluate(evaluator_input, evaluator_data) 
	assert result == {'message': '', 'passed': True}