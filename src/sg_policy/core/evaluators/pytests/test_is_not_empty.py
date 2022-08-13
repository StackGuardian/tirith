import is_not_empty as notempty

input = 'abc'

a = notempty.IsNotEmpty()

def test_evaluate():
	result = a.evaluate(input) 
	assert result == {"passed": True, "message": ""}