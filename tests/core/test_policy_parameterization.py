import pytest
import json
from subprocess import Popen, PIPE

from tirith.core.policy_parameterization import get_policy_with_vars_replaced, _VariableNotFound


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
    return get_policy_with_vars_replaced(input_dict, var_dict)


def test_nested_dict(processed_policy):
    assert processed_policy[0]["meta"]["required_provider"] == "stackguardian/json"


def test_var_value_in_list(processed_policy):
    assert processed_policy[0]["evaluators"][0]["condition"]["value"] == 2


def test_eval_expression_parameterization(processed_policy):
    assert processed_policy[0]["eval_expression"] == "check0"


def test_not_found_variable(processed_policy):
    assert processed_policy[1] == ["key_path"]


# TODO: Create testcases for:
# - test inline vars precendece over var files
# - test undefined vars
# - test var syntax is not valid
# - test with var files
# - test with var files and inline vars together
# - test with var files and inline vars overlapping
def test_e2e_inline_vars():
    # Run the tirith binary with the inline variables
    process = Popen(
        [
            "tirith",
            "-policy-path",
            "tests/core/fixtures/policy_parametrized.json",
            "-input-path",
            "tests/core/fixtures/input.json",
            "-var",
            'city={"name": "New York"}',
            "--json",
        ],
        stdout=PIPE,
        stderr=PIPE,
    )
    stdout, stderr = process.communicate()
    tirith_result = json.loads(stdout)
    assert tirith_result["final_result"] is True
    assert process.returncode == 0
    assert stderr == b""
