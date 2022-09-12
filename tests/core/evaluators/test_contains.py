from sg_policy.core.evaluators import ContainedIn
from pytest import mark


checks_passing = [
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

checks_failing = [
    (["a", "b", "c", "d"], "e"),
    ("e", ["a", "b", "c", "d"]),
    (["a"], "a"),
    (2, "a"),
    ("3", 3),
    ("c", ["a", "b"]),
]

checks_unsupported = [
    (2, "a"),
    ("3", 3),
    (1, 1),
    (1, 2),
    (["a"], ["a", "b", "c", "d"]),
]

evaluator = ContainedIn()

# pytest -v -m passing
@mark.passing
@mark.parametrize("evaluator_input,evaluator_data", checks_passing)
def test_evaluate_passing(evaluator_input, evaluator_data):
    result = evaluator.evaluate(evaluator_input, evaluator_data)
    assert result["passed"] == True  # {"passed": True, "message": f"Found {evaluator_input} inside {evaluator_data}"}


# # pytest -v -m failing
@mark.failing
@mark.parametrize("evaluator_input,evaluator_data", checks_failing)
def test_evaluate_failing(evaluator_input, evaluator_data):
    result = evaluator.evaluate(evaluator_input, evaluator_data)
    assert (
        result["passed"] == False
    )  # {"passed": True, "message": f"Failed to find {evaluator_input} inside {evaluator_data}"}


# pytest -v -m failing
@mark.failing
@mark.parametrize("evaluator_input,evaluator_data", checks_unsupported)
def test_evaluate_unsupported(evaluator_input, evaluator_data):
    result = evaluator.evaluate(evaluator_input, evaluator_data)
    assert (
        result["passed"] == False
    )  # {"passed": True, "message": f"Failed to find {evaluator_input} inside {evaluator_data}"}
