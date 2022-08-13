import less_than as less

input = {'value': 5}
condition = 10

a = less.LessThan()

def test_evaluate():
	result = a.evaluate(input, condition) 
	assert result == {"passed": True, "message": ""}
