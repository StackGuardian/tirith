import equals as equals

input = {1,2,3,4}
condition = {1,2,3,4}

a = equals.Equals()

def test_evaluate():
	result = a.evaluate(input, condition) 
	assert result == {"passed": True, "message": ""}