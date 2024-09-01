import re
import pydash


class PydashPathNotFound:
    pass


def check_match(string: str, pattern: re.Pattern) -> re.Match:
    match_ = re.fullmatch(pattern, string)
    return match_


def helper(dictionary: dict, var_pattern: re.Pattern, var_dict: dict):
    for key, value in dictionary.items():
        if isinstance(value, str):
            match = check_match(value, var_pattern)
            if bool(match):
                dictionary[key] = pydash.get(var_dict, match.group(1), default=PydashPathNotFound)


def replace_vars(policy_dict: dict, var_dict: dict) -> dict:
    var_pattern = re.compile(r"{{var\.([\w\.]+)}}")

    evaluators = policy_dict["evaluators"]
    helper(policy_dict["meta"], var_pattern, var_dict)
    for i in range(len(evaluators)):
        match = check_match(evaluators[i]["id"], var_pattern)
        if bool(match):
            evaluators[i]["id"] = pydash.get(var_dict, match.group(1), default=PydashPathNotFound)

        helper(evaluators[i]["condition"], var_pattern, var_dict)
        helper(evaluators[i]["provider_args"], var_pattern, var_dict)

    match = check_match(policy_dict["eval_expression"], var_pattern)
    if bool(match):
        policy_dict["eval_expression"] = pydash.get(var_dict, match.group(1), default=PydashPathNotFound)

    return policy_dict
