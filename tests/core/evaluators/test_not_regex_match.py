import pytest
from pytest import mark

from tirith.core.evaluators import NotRegexMatch
from tirith.utils import json_format_value

evaluator = NotRegexMatch()


# pytest -v -m passing
@mark.passing
def test_not_regex_passing():
    evaluator_input = "amitrakshar01"
    evaluator_data = r"^\d+$"
    result = evaluator.evaluate(evaluator_input, evaluator_data)
    assert result == {
        "passed": True,
        "message": f"{json_format_value(evaluator_input)} does not match regex pattern {json_format_value(evaluator_data)}",
    }


# pytest -v -m failing
@mark.failing
def test_not_regex_failing():
    evaluator_input = "12345"
    evaluator_data = r"^\d+$"
    result = evaluator.evaluate(evaluator_input, evaluator_data)
    assert result == {
        "passed": False,
        "message": f"{json_format_value(evaluator_input)} matches regex pattern {json_format_value(evaluator_data)}",
    }


def test_not_regex_list():
    result = evaluator.evaluate(evaluator_input=["something"], evaluator_data=r"^\d+$")
    assert result["passed"] is True


def test_not_regex_dict():
    result = evaluator.evaluate(evaluator_input=dict(a=2), evaluator_data=r"^\d+$")
    assert result["passed"] is True


def test_not_regex_invalid_pattern():
    result = evaluator.evaluate(evaluator_input="something", evaluator_data="[unterminated")
    assert result["passed"] is False
    assert (
        "unterminated" in result["message"]
        or "unexpected end" in result["message"]
        or "nothing to repeat" in result["message"]
    )


@pytest.mark.parametrize(
    "evaluator_input, evaluator_data, expected_passed",
    [
        # 1. List input where the regex DOES match -> passed=False
        (["something", "else"], r"something", False),
        # 2. Dict input where the regex DOES match -> passed=False
        ({"key": "value"}, r"key", False),
        # 3. Partial/substring regex match -> passed=False
        ("hello world", r"world", False),
        # 4. Partial/substring non-match -> passed=True
        ("hello world", r"planet", True),
        # 5. Anchored regex (^...$) match and non-match
        ("hello world", r"^hello world$", False),
        ("hello world", r"^world", True),
        ("hello world", r"hello$", True),
        # 6. Multiline string regex match -> passed=False
        ("line1\nline2\nline3", r"line2", False),
        # 7. Multiline string regex non-match -> passed=True
        ("line1\nline2\nline3", r"line4", True),
        # 8. Empty string with a non-empty regex -> passed=True
        ("", r"non-empty", True),
        # 9. Empty regex pattern -> passed=False because re.search("", value) matches
        ("any string", r"", False),
        # 10. Regex patterns involving special/escaped characters
        ("a.b*c+d?e[f](g){h}i", r"b\*c\+d\?e\[f\]\(g\)\{h\}i", False),
        ("a.b*c+d?e[f](g){h}i", r"b\*c\+d\?e\[f\]\(z\)\{h\}i", True),
        # 11. Case-sensitive matching behavior
        ("Hello World", r"hello", True),
        ("Hello World", r"Hello", False),
    ],
)
def test_not_regex_match_parametrizations(evaluator_input, evaluator_data, expected_passed):
    result = evaluator.evaluate(evaluator_input, evaluator_data)
    assert result["passed"] is expected_passed


@pytest.mark.parametrize(
    "evaluator_input",
    [
        # 12. Unsupported input type such as integer -> passed=False
        123,
        True,
        None,
        45.67,
    ],
)
def test_not_regex_match_unsupported_input_types(evaluator_input):
    result = evaluator.evaluate(evaluator_input, r"^\d+$")
    assert result["passed"] is False


@pytest.mark.parametrize(
    "evaluator_data",
    [
        # 13. Unsupported evaluator_data type such as integer -> passed=False
        123,
        True,
        None,
        45.67,
        ["list"],
        {"dict": "val"},
    ],
)
def test_not_regex_match_unsupported_evaluator_data_types(evaluator_data):
    result = evaluator.evaluate("some string", evaluator_data)
    assert result["passed"] is False


@pytest.mark.parametrize(
    "malformed_regex",
    [
        # 14. Multiple malformed regex patterns
        "[unterminated",
        "(missing closing parenthesis",
        "\\",
        "*nothing to repeat",
    ],
)
def test_not_regex_match_multiple_malformed_regex_patterns(malformed_regex):
    result = evaluator.evaluate("some string", malformed_regex)
    assert result["passed"] is False
    assert "message" in result

    msg = result["message"]
    assert bool(msg), "Error message should not be empty"
    assert msg != "Not evaluated", "Evaluator did not run"
    assert "matches regex pattern" not in msg, "Should not be a normal evaluation message"
    assert "unsupported data type" not in msg, "Should not be a type error message"
