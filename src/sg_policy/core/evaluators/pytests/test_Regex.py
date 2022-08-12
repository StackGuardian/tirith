import re
import pytest
import sys
sys.path.append('/policy-framework/src/sg_policy/core/evaluators')
import regex as regex

evaluator_data = "^(?=[a-zA-Z0-9._]{8,20}$)(?!.*[_.]{2})[^_.].*[^_.]$"
evaluator_input = "amitrakshar01"
# def test_regexEquals(evaluator_data, evaluator_input):
#     # assert re.match(evaluator_data, evaluator_input) is not None
#     assert True

a = regex.RegexEquals()
def test_regex():
    result = a.evaluate(evaluator_input, evaluator_data)
    assert result == {"result": True, "message": ""}
    # assert a.evaluate(evaluator_input, evaluator_data) is False