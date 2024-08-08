from pytest import mark

from tirith.core.evaluators import NotContains

checks_failing = [
    (["a", "b", "c", "d"], "a"),
    ("a", "a"),
    ("minura", "a"),
    ({"a": "val1", "b": "val2"}, "a"),
    ({"b": 6, "a": 2, "c": 16}, {"a": 2, "b": 6}),
    ({"b": 6, "a": 2, "c": 16}, {"a": 2}),
    ({"b": 6, "a": ["a", "d"], "c": 16}, {"a": ["a", "d"], "b": 6}),
    ({"b": 6, "a": [{"a": 2}, "d"], "c": 16}, {"a": [{"a": 2}, "d"], "b": 6}),
    (["a", "b"], "a"),
    (["a", "b"], "b"),
    (["a", ["b"]], ["b"]),
    (["a"], "a"),
    ("c", ["a", "b"]),
]

checks_passing = [
    (["a", "b", "c", "d"], "e"),
    (["a", "b", "c", "d"], ["a"]),
    (["a", "b"], "c"),
    ({"b": 8, "a": ["a", "c"], "c": 16}, {"a": ["a", "d"], "b": 6}),
    ({"a": "val1", "b": "val2"}, "c"),
]

checks_unsupported = [(2, "a"), ("3", 3), (1, 1), (1, 2), ("e", ["a", "b", "c", "d"])]

evaluator = NotContains()


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
