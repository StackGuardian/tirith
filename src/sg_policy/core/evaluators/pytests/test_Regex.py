import re
import pytest
import sys
sys.path.append('/home/aksharsans/Desktop/SG_policyframework/policy-framework/src/sg_policy/core/evaluators')
import Regex

evaluator_data = "^(?=[a-zA-Z0-9._]{8,20}$)(?!.*[_.]{2})[^_.].*[^_.]$"
evaluator_input = "amitrakshar01"
# def test_regexEquals(evaluator_data, evaluator_input):
#     # assert re.match(evaluator_data, evaluator_input) is not None
#     assert True

a = Regex.regexEquals()
def test_regex():
    assert a.evaluate(evaluator_input, evaluator_data) is True
    # assert a.evaluate(evaluator_input, evaluator_data) is False