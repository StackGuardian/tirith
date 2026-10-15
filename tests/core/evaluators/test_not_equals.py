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


@mark.parametrize(
    "evaluator_input,evaluator_data,passed,message",
    [
        ({"a": 1, "b": 2}, {"b": 2, "a": 1}, False, '`{"a": 1, "b": 2}` is equal to `{"b": 2, "a": 1}`'),
        ([[1, 2], [3, 4]], [[1, 2], [3, 4]], False, "`[[1, 2], [3, 4]]` is equal to `[[1, 2], [3, 4]]`"),
        ([[1, 2]], [[1, 3]], True, "`[[1, 2]]` is not equal to `[[1, 3]]`"),
        ("1", 1, True, '`"1"` is not equal to `1`'),
        (None, None, False, "`null` is equal to `null`"),
        (None, 1, True, "`null` is not equal to `1`"),
        (True, 1, False, "`true` is equal to `1`"),
    ],
    ids=[
        "dict-key-order",
        "nested-lists-equal",
        "nested-lists-different",
        "str-vs-int",
        "none-equal",
        "none-unequal",
        "true-vs-one",
    ],
)
def test_evaluate_edge_cases(evaluator_input, evaluator_data, passed, message):
    assert evaluator.evaluate(evaluator_input, evaluator_data) == {"passed": passed, "message": message}

