from pytest import mark

from tirith.core.evaluators import IsEmpty

checks_passing = ("", None, [], dict())
checks_failing = ("stackguardian", 1, [None], dict(a=1))

evaluator = IsEmpty()


@mark.passing
@mark.parametrize("evaluator_input", checks_passing)
def test_evaluate_passing(evaluator_input):
    result = evaluator.evaluate(evaluator_input)
    assert result == {"message": f"{evaluator_input} is empty", "passed": True}


@mark.passing
@mark.parametrize("evaluator_input", checks_failing)
def test_evaluate_failing(evaluator_input):
    result = evaluator.evaluate(evaluator_input)
    assert result == {"message": f"{evaluator_input} is not empty", "passed": False}
