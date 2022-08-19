import re
import pytest
import sys
sys.path.append('/policy-framework/src/sg_policy/core/evaluators')
import regex as regex

evaluator_data1 = "^(?=[a-zA-Z0-9._]{8,20}$)(?!.*[_.]{2})[^_.].*[^_.]$"
evaluator_input1 = "amitrakshar01"

evaluator_data2 = "^(?=[a-zA-Z0-9._]{8,20}$)(?!.*[_.]{2})[^_.].*[^_.]$"
evaluator_input2 = "@01amitrakshar"

a = regex.RegexEquals()

#pytest -v -m passing
@pytest.mark.passing
def test_regex_passing():
    result = a.evaluate(evaluator_input1, evaluator_data1)
    assert result == {"result": True, "message": ""}
    
#pytest -v -m failing
@pytest.mark.failing
def test_regex_failing():
    result = a.evaluate(evaluator_input2, evaluator_data2)
    assert result == {"result": True, "message": ""}