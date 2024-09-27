# Maintain all core related tests here
from pytest import mark

from tirith.core.core import final_evaluator


@mark.passing
def test_final_evaluator_skipped_check_should_be_removed() -> None:
    actual_result = final_evaluator("!skipped_check && passing_check", dict(skipped_check=None, passing_check=True))
    assert actual_result == (True, [])

    actual_result = final_evaluator("!skipped_check && passing_check", dict(skipped_check=None, passing_check=False))
    assert actual_result == (False, [])


@mark.passing
def test_final_evaluator_undef_var_should_be_removed_from_exp() -> None:
    actual_result = final_evaluator(
        "!skipped_check && passing_check || undefined_check", dict(skipped_check=None, passing_check=True)
    )
    assert actual_result == (
        True,
        ["The following evaluator ids are not defined and have been removed: undefined_check"],
    )

    actual_result = final_evaluator(
        "!skipped_check && passing_check || undefined_check", dict(skipped_check=None, passing_check=False)
    )
    assert actual_result == (
        False,
        ["The following evaluator ids are not defined and have been removed: undefined_check"],
    )


@mark.passing
def test_final_evaluator_malicious_eval_should_err() -> None:
    actual_result = final_evaluator(
        "!skipped_check && passing_check || [].__class__.__base__", dict(skipped_check=None, passing_check=True)
    )
    assert actual_result == (False, ["The following symbols are not allowed: __class__, __base__"])
