import re
import pytest
import Regex

evaluator_data = "^(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}$"
evaluator_input = "123-456"
# def test_regexEquals(evaluator_data, evaluator_input):
#     # assert re.match(evaluator_data, evaluator_input) is not None
#     assert True

test_regex = Regex.regexEquals(evaluator_data, evaluator_input)
assert test_regex.evaluate() is True

