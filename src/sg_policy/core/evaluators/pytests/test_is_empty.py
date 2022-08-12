import is_empty as empty

input = ''

a = empty.IsEmpty()

def test_evaluate():
	result = a.evaluate(input) 
	assert result == {'message': '', 'passed': True}
	
