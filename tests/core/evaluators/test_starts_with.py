from tirith.core.evaluators import StartsWith

evaluator = StartsWith()


def test_starts_with_passes():
    assert evaluator.evaluate("acme-bucket", "acme-") == {
        "passed": True,
        "message": "acme-bucket starts with acme-",
    }


def test_starts_with_fails():
    assert evaluator.evaluate("other-bucket", "acme-") == {
        "passed": False,
        "message": "other-bucket does not start with acme-",
    }


def test_starts_with_empty_prefix():
    assert evaluator.evaluate("anything", "") == {
        "passed": True,
        "message": "anything starts with ",
    }


def test_starts_with_empty_input():
    assert evaluator.evaluate("", "acme-") == {
        "passed": False,
        "message": " does not start with acme-",
    }


def test_starts_with_non_string_input_names_type():
    result = evaluator.evaluate(42, "acme-")
    assert result["passed"] is False
    assert "int" in result["message"]
