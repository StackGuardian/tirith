from tirith.core.evaluators import NotEquals
from pytest import mark

checks_failing = [({1, 2, 3, 4}, {1, 2, 3, 4}), ([2, 4, 3], [2, 3, 4])]

checks_passing = [({1, 2, 3, 4}, {2, 3, 4}), ({2, 3, 4}, [2, 3, 4])]

evaluator = NotEquals()


# pytest -v -m passing
@mark.passing
@mark.parametrize("evaluator_input,evaluator_data", checks_passing)
def test_evaluate_passing(evaluator_input, evaluator_data):
    result = evaluator.evaluate(evaluator_input, evaluator_data)
    assert result == {"passed": True, "message": f"`{evaluator_input}` is not equal to `{evaluator_data}`"}


# pytest -v -m failing
@mark.failing
@mark.parametrize("evaluator_input,evaluator_data", checks_failing)
def test_evaluate_failing(evaluator_input, evaluator_data):
    result = evaluator.evaluate(evaluator_input, evaluator_data)
    assert result == {"passed": False, "message": f"`{evaluator_input}` is equal to `{evaluator_data}`"}
