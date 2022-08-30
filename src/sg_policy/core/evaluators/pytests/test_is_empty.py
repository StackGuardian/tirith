import is_empty as empty
import pytest

evaluator_input1 = ""
evaluator_input2 = "stackguardian"

a = empty.IsEmpty()

# pytest -v -m passing
@pytest.mark.passing
def test_evaluate_passing():
    result = a.evaluate(evaluator_input1)
    assert result == {"message": "The evaluation passed successfully", "passed": True}


# pytest -v -m failing
@pytest.mark.failing
def test_evaluate_failing():
    result = a.evaluate(evaluator_input2)
    assert result == {"message": "The evaluation passed successfully", "passed": True}
