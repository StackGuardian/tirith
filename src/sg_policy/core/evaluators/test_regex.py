import re
import pytest

evaluator_data = "^(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}$"
evaluator_input = "123-456"
def test_evaluator(evaluator_data, evaluator_input):
    assert re.match(evaluator_data, evaluator_input) is not None

