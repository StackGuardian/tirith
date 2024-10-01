import re
import pydash

from typing import List, Tuple

_VAR_PATTERN = re.compile(r"{{\s*var\.([\w\.]+)\s*}}")


class _VariableNotFound:
    pass


def _replace_vars_in_dict(dictionary: dict, var_dict: dict, not_found_vars: List[str]):
    """
    Replace the variables in the dictionary with the values from the var_dict

    :param dictionary:   The dictionary to replace the variables in
    :param var_pattern:  The pattern to match the variables
    :param var_dict:     The dictionary containing the variables
    """
    for key, value in dictionary.items():
        if not isinstance(value, str):
            continue
        _replace_var_in_dict(dictionary, key, var_dict, not_found_vars)


def _replace_var_in_dict(dictionary: dict, key: str, var_dict: dict, not_found_vars: list):
    """
    Replace the variable in the dictionary with the value from the var_dict
    This only replaces single dictionary key

    :param dictionary:     The dictionary to replace the variable in
    :param key:            The key of the param `dictionary` to replace the variable in
    :param var_dict:       The dictionary containing the variables
    :param not_found_vars: The list to store the variables that are not found in
    """
    var_expression = dictionary[key]

    match = _VAR_PATTERN.match(var_expression)
    if not match:
        return

    var_name = match.group(1)
    var_value = pydash.get(var_dict, var_name, default=_VariableNotFound)
    if var_value is _VariableNotFound:
        not_found_vars.append(var_name)
        return
    dictionary[key] = var_value


def get_policy_with_vars_replaced(policy_dict: dict, var_dict: dict) -> Tuple[dict, List[str]]:
    """
    Replace the variables in the policy_dict with the values from the var_dict

    :param policy_dict: The policy dictionary
    :param var_dict:    The dictionary containing the variables
    :return:            The policy dictionary with the variables replaced
                        and the list of variables that are not found
    """
    not_found_vars = []
    # Replace vars in the meta key
    _replace_vars_in_dict(policy_dict["meta"], var_dict, not_found_vars)

    # Replace vars in the evaluators
    evaluators = policy_dict["evaluators"]
    for evaluator in evaluators:
        _replace_var_in_dict(evaluator, "id", var_dict, not_found_vars)
        _replace_vars_in_dict(evaluator["provider_args"], var_dict, not_found_vars)
        _replace_vars_in_dict(evaluator["condition"], var_dict, not_found_vars)

    # Replace vars in the eval_expression
    _replace_var_in_dict(policy_dict, "eval_expression", var_dict, not_found_vars)

    return policy_dict, not_found_vars
