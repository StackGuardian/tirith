from sg_policy.core.evaluators import Contains
from pytest import mark


checks_passing = [(["a", "b", "c", "d"], "a"), ("a", "a"), (1, 1), (1, 2), (["a"], ["a", "b", "c", "d"])]

checks_failing = [
    (["a", "b", "c", "d"], "e"),
    (["a"], "a"),
    (2, "a"),
    ("3", 3),
    ("a", ["a", "b"]),
    ("b", ["a", "b"]),
    ("c", ["a", "b"]),
]

checks_unsupported = [
    (["a", "b", "c", "d"], "e"),
    (["a"], "a"),
    (2, "a"),
    ("3", 3),
    ("a", ["a", "b"]),
    ("b", ["a", "b"]),
    ("c", ["a", "b"]),
]

evaluator = Contains()

# pytest -v -m passing
@mark.passing
@mark.parametrize("evaluator_input,evaluator_data", checks_passing)
def test_evaluate_passing(evaluator_input, evaluator_data):
    result = evaluator.evaluate(evaluator_input, evaluator_data)
    assert result == {"passed": True, "message": f"Found {evaluator_input} inside {evaluator_data}"}


# pytest -v -m failing
@mark.failing
@mark.parametrize("evaluator_input,evaluator_data", checks_failing)
def test_evaluate_failing(evaluator_input, evaluator_data):
    result = evaluator.evaluate(evaluator_input, evaluator_data)
    assert result == {"passed": True, "message": f"Failed to find {evaluator_input} inside {evaluator_data}"}


# pytest -v -m failing
@mark.failing
@mark.parametrize("evaluator_input,evaluator_data", checks_failing)
def test_evaluate_unsupported(evaluator_input, evaluator_data):
    result = evaluator.evaluate(evaluator_input, evaluator_data)
    assert result == {"passed": True, "message": f"Failed to find {evaluator_input} inside {evaluator_data}"}
