from tirith.core.evaluators import NotContainedIn
from pytest import mark


checks_failing = [
    ("a", ["a", "b", "c", "d"]),
    ("a", "a"),
    ("a", "minura"),
    ("a", {"a": "val1", "b": "val2"}),
    ({"a": 2, "b": 6}, {"b": 6, "a": 2, "c": 16}),
    ({"a": 2}, {"b": 6, "a": 2, "c": 16}),
    ({"a": ["a", "d"], "b": 6}, {"b": 6, "a": ["a", "d"], "c": 16}),
    ({"a": [{"a": 2}, "d"], "b": 6}, {"b": 6, "a": [{"a": 2}, "d"], "c": 16}),
    ("a", ["a", "b"]),
    ("b", ["a", "b"]),
    (["b"], ["a", ["b"]]),
]

checks_passing = [
    ("e", ["a", "b", "c", "d"]),
    (["a"], ["a", "b", "c", "d"]),
    ("c", ["a", "b"]),
    ({"a": ["a", "d"], "b": 6}, {"b": 8, "a": ["a", "c"], "c": 16}),
    ("c", {"a": "val1", "b": "val2"}),
]

checks_unsupported = [
    (2, "a"),
    ("3", 3),
    (1, 1),
    (1, 2),
    (["a", "b", "c", "d"], "e"),
]

evaluator = NotContainedIn()


# pytest -v -m passing
@mark.passing
@mark.parametrize("evaluator_input,evaluator_data", checks_passing)
def test_evaluate_passing(evaluator_input, evaluator_data):
    result = evaluator.evaluate(evaluator_input, evaluator_data)
    assert result["passed"] == True
    assert "Did not find" in result["message"]


# # pytest -v -m failing
@mark.failing
@mark.parametrize("evaluator_input,evaluator_data", checks_failing)
def test_evaluate_failing(evaluator_input, evaluator_data):
    result = evaluator.evaluate(evaluator_input, evaluator_data)
    assert result["passed"] == False
    assert "Found" in result["message"]


# pytest -v -m failing
@mark.failing
@mark.parametrize("evaluator_input,evaluator_data", checks_unsupported)
def test_evaluate_unsupported(evaluator_input, evaluator_data):
    result = evaluator.evaluate(evaluator_input, evaluator_data)
    assert result["passed"] == False
    assert "is an unsupported data type for evaluating against value in 'condition.value" in result["message"]
