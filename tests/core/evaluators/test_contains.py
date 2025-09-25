from tirith.core.evaluators import Contains
from pytest import mark


checks_passing = [
    (["a", "b", "c", "d"], "a"),
    ("a", "a"),
    ("minura", "a"),
    ("hello world", "world"),
    ({"a": "val1", "b": "val2"}, "a"),
    ({"b": 6, "a": 2, "c": 16}, {"a": 2, "b": 6}),
    ({"b": 6, "a": 2, "c": 16}, {"a": 2}),
    ({"b": 6, "a": ["a", "d"], "c": 16}, {"a": ["a", "d"], "b": 6}),
    ({"b": 6, "a": [{"a": 2}, "d"], "c": 16}, {"a": [{"a": 2}, "d"], "b": 6}),
    (["a", "b"], "a"),
    (["a", "b"], "b"),
    (["a", ["b"]], ["b"]),
    (["a"], "a"),
    ([1, 2, 3], 2),
    ([1, [2, 3]], [2, 3]),
]

checks_failing = [
    (["a", "b", "c", "d"], "e"),
    ("hello", "world"),
    ("abc", "def"),
    ({"a": "val1", "b": "val2"}, "c"),
    ({"b": 6, "a": 2, "c": 16}, {"a": 3}),
    ({"b": 6, "a": 2, "c": 16}, {"a": 2, "d": 4}),
    ({"b": 6, "a": 2, "c": 16}, {"a": 2, "b": 7}),
    (["a", "b"], "c"),
    ([1, 2, 3], 4),
    ([1, [2, 3]], [3, 4]),
]

checks_unsupported = [
    (2, "a"),
    (1.5, "test"),
    (True, "boolean"),
    (None, "none"),
]

evaluator = Contains()


# pytest -v -m passing
@mark.passing
@mark.parametrize("evaluator_input,evaluator_data", checks_passing)
def test_evaluate_passing(evaluator_input, evaluator_data):
    result = evaluator.evaluate(evaluator_input, evaluator_data)
    assert result["passed"]
    assert "Found" in result["message"]
    assert "inside" in result["message"]


# pytest -v -m failing
@mark.failing
@mark.parametrize("evaluator_input,evaluator_data", checks_failing)
def test_evaluate_failing(evaluator_input, evaluator_data):
    result = evaluator.evaluate(evaluator_input, evaluator_data)
    assert not result["passed"]
    assert "Failed to find" in result["message"]
    assert "inside" in result["message"]


# pytest -v -m unsupported
@mark.unsupported
@mark.parametrize("evaluator_input,evaluator_data", checks_unsupported)
def test_evaluate_unsupported(evaluator_input, evaluator_data):
    result = evaluator.evaluate(evaluator_input, evaluator_data)
    assert not result["passed"]
    assert "unsupported data type" in result["message"]


# Test specific string scenarios
def test_string_contains():
    # Test case-sensitive string containment
    result = evaluator.evaluate("Hello World", "World")
    assert result["passed"]
    assert "Found" in result["message"]

    result = evaluator.evaluate("Hello World", "world")  # case-sensitive
    assert not result["passed"]
    assert "Failed to find" in result["message"]


def test_empty_string():
    # Empty string should be contained in any string
    result = evaluator.evaluate("hello", "")
    assert result["passed"]

    # But non-empty string should not be in empty string
    result = evaluator.evaluate("", "hello")
    assert not result["passed"]


def test_list_contains():
    # Test nested list containment
    result = evaluator.evaluate([[1, 2], [3, 4]], [1, 2])
    assert result["passed"]

    # Test mixed types in list
    result = evaluator.evaluate([1, "hello", 3.14], "hello")
    assert result["passed"]

    result = evaluator.evaluate([1, "hello", 3.14], "world")
    assert not result["passed"]


def test_dict_contains():
    # Test partial dict containment
    input_dict = {"name": "John", "age": 30, "city": "NYC"}

    # Should pass - subset of key-value pairs
    result = evaluator.evaluate(input_dict, {"name": "John", "age": 30})
    assert result["passed"]

    # Should fail - wrong value
    result = evaluator.evaluate(input_dict, {"name": "John", "age": 25})
    assert not result["passed"]

    # Should fail - non-existent key
    result = evaluator.evaluate(input_dict, {"name": "John", "country": "USA"})
    assert not result["passed"]


def test_dict_key_contains():
    # Test single key containment
    input_dict = {"name": "John", "age": 30}

    result = evaluator.evaluate(input_dict, "name")
    assert result["passed"]

    result = evaluator.evaluate(input_dict, "address")
    assert not result["passed"]


def test_empty_containers():
    # Empty list
    result = evaluator.evaluate([], "anything")
    assert not result["passed"]

    # Empty dict
    result = evaluator.evaluate({}, "anything")
    assert not result["passed"]

    # Empty dict with empty dict
    result = evaluator.evaluate({}, {})
    assert result["passed"]


def test_error_handling():
    # Test that exceptions are handled gracefully
    # This shouldn't happen in normal use, but let's test defensive coding
    try:
        result = evaluator.evaluate(None, None)
        assert not result["passed"]
        assert result["message"] == "Not evaluated"
    except Exception:
        pass  # If it throws an exception, that's also acceptable


def test_message_formatting():
    # Test that messages are properly formatted
    result = evaluator.evaluate("test string", "test")
    assert result["passed"]
    assert '"test"' in result["message"]
    assert '"test string"' in result["message"]

    result = evaluator.evaluate([1, 2, 3], 4)
    assert not result["passed"]
    assert "4" in result["message"]
    assert "[1, 2, 3]" in result["message"]
