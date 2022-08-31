from sg_policy.core.evaluators import Contains
from pytest import mark

evaluator_data1 = ["a", "b", "c", "d"]
evaluator_input1 = "a"

evaluator_data2 = ["a", "b", "c", "d"]
evaluator_input2 = "e"

evaluator = Contains()

# pytest -v -m passing
@mark.passing
def test_evaluate_passing():
    result = evaluator.evaluate(evaluator_input1, evaluator_data1)
    assert result == {"passed": True, "message": f"Found {evaluator_input1} inside {evaluator_data1}"}


# pytest -v -m failing
@mark.failing
def test_evaluate_failing():
    result = evaluator.evaluate(evaluator_input2, evaluator_data2)
    assert result == {"passed": True, "message": f"Failed to find {evaluator_input2} inside {evaluator_data2}"}
