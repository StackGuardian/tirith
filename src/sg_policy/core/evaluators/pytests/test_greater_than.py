import greater_than as greater

input = {'value': 5}
condition = 2

a = greater.GreaterThan()

def test_evaluate():
	result = a.evaluate(input, condition) 
	assert result == {"passed": True, "message": ""}
