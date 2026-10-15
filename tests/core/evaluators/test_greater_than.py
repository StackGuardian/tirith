from tirith.core.evaluators import GreaterThan
from pytest import mark

evaluator_input1 = 5
evaluator_data1 = 2

evaluator_input2 = 5
evaluator_data2 = 9

evaluator = GreaterThan()


# pytest -v -m passing
@mark.passing
def test_evaluate_passing():
    result = evaluator.evaluate(evaluator_input1, evaluator_data1)
    assert result == {"passed": True, "message": f"`{evaluator_input1}` is greater than `{evaluator_data1}`"}


# pytest -v -m failing
@mark.failing
def test_evaluate_failing():
    result = evaluator.evaluate(evaluator_input2, evaluator_data2)
    assert result == {"passed": False, "message": f"`{evaluator_input2}` is not greater than `{evaluator_data2}`"}


@mark.parametrize(
    "value,other,passed,message",
    [
        (5, 5, False, "`5` is not greater than `5`"),
        (1.5, 1.25, True, "`1.5` is greater than `1.25`"),
        (1.25, 1.5, False, "`1.25` is not greater than `1.5`"),
        (2.5, 2, True, "`2.5` is greater than `2`"),
    ],
    ids=["equal", "greater-floats", "lesser-floats", "float-and-integer"],
)
def test_evaluate_numeric_edge_cases(value, other, passed, message):
    assert evaluator.evaluate(value, other) == {"passed": passed, "message": message}


@mark.failing
@mark.parametrize(
    "value,other,message",
    [
        (None, 1, "'>' not supported between instances of 'NoneType' and 'int'"),
        (None, None, "'>' not supported between instances of 'NoneType' and 'NoneType'"),
        ("5", 5, "'>' not supported between instances of 'str' and 'int'"),
        (5, "5", "'>' not supported between instances of 'int' and 'str'"),
    ],
    ids=["none-and-number", "none-and-none", "string-and-number", "number-and-string"],
)
def test_evaluate_invalid_comparisons(value, other, message):
    assert evaluator.evaluate(value, other) == {"passed": False, "message": message}
