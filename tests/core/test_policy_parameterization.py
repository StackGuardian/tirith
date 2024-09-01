import pytest

from tirith.core.policy_parameterization import replace_vars, PydashPathNotFound

@pytest.fixture
def processed_policy():
    var_dict = {
        "var_1": {"A": [1, 2, 3, 4, 5, 6]},
        "var_2": "check0",
        "providers": {"json": "stackguardian/json", "infracost": "stackguardian/infracost"},
    }

    input_dict = {
        "meta": {"version": "", "required_provider": "{{var.providers.json}}"},
        "evaluators": [
            {
                "id": "check0",
                "provider_args": {
                    "operation_type": "get_value",
                    "key_path": "{{var.key_path}}",
                },
                "condition": {"type": "Equals", "value": "{{var.var_1.A.1}}"},
            }
        ],
        "eval_expression": "{{var.var_2}}",
    }

    # Run the function once and return the result
    return replace_vars(input_dict, var_dict)


def test_nested_dict(processed_policy):
    assert processed_policy["meta"]["required_provider"] == "stackguardian/json"


def test_path_not_found(processed_policy):
    assert processed_policy["evaluators"][0]["provider_args"]["key_path"] == PydashPathNotFound


def test_var_value_in_list(processed_policy):
    assert processed_policy["evaluators"][0]["condition"]["value"] == 2


def test_eval_expression_parameterization(processed_policy):
    assert processed_policy["eval_expression"] == "check0"
