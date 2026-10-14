from tirith.core.evaluators import EndsWith

evaluator = EndsWith()


def test_ends_with_passes():
    assert evaluator.evaluate("ami-hardened", "-hardened") == {
        "passed": True,
        "message": "ami-hardened ends with -hardened",
    }


def test_ends_with_fails():
    assert evaluator.evaluate("ami-default", "-hardened") == {
        "passed": False,
        "message": "ami-default does not end with -hardened",
    }


def test_ends_with_empty_suffix():
    assert evaluator.evaluate("anything", "") == {
        "passed": True,
        "message": "anything ends with ",
    }


def test_ends_with_empty_input():
    assert evaluator.evaluate("", "-hardened") == {
        "passed": False,
        "message": " does not end with -hardened",
    }


def test_ends_with_non_string_input_names_type():
    result = evaluator.evaluate(42, "-hardened")
    assert result["passed"] is False
    assert "int" in result["message"]
