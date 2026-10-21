"""Provider metadata spelling and backward compatibility."""

from pytest import mark

from tirith.core.core import start_policy_evaluation_from_dict


def _policy(meta):
    return {
        "meta": {"version": "v1", **meta},
        "evaluators": [
            {
                "id": "check0",
                "provider_args": {"operation_type": "get_value", "key_path": "a"},
                "condition": {"type": "Equals", "value": 1},
            }
        ],
        "eval_expression": "check0",
    }


@mark.passing
def test_meta_provider_is_accepted():
    result = start_policy_evaluation_from_dict(_policy({"provider": "stackguardian/json"}), {"a": 1})

    assert result["final_result"] is True
    assert result["meta"]["required_provider"] == "stackguardian/json"


@mark.passing
def test_legacy_meta_required_provider_still_works():
    result = start_policy_evaluation_from_dict(_policy({"required_provider": "stackguardian/json"}), {"a": 1})

    assert result["final_result"] is True
    assert result["meta"]["required_provider"] == "stackguardian/json"


@mark.passing
def test_meta_provider_takes_precedence_when_both_are_present():
    result = start_policy_evaluation_from_dict(
        _policy(
            {
                "provider": "stackguardian/json",
                "required_provider": "stackguardian/does-not-exist",
            }
        ),
        {"a": 1},
    )

    assert result["final_result"] is True
    assert result["meta"]["required_provider"] == "stackguardian/json"


@mark.passing
def test_result_metadata_is_identical_for_both_input_spellings():
    canonical = start_policy_evaluation_from_dict(_policy({"provider": "stackguardian/json"}), {"a": 1})
    legacy = start_policy_evaluation_from_dict(_policy({"required_provider": "stackguardian/json"}), {"a": 1})

    assert canonical["meta"] == legacy["meta"]
