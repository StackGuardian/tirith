import re


def check_match(string: str, pattern: re.Pattern) -> re.Match:
    match_ = re.fullmatch(pattern, string)
    return match_


# traversing var_dict (esp for nested cases)
def get_var(data: dict, path: str):
    keys = path.split(".")
    value = data
    for key in keys:
        value = value[key]
    return value


def replace_vars(policy_dict: dict, var_dict: dict) -> dict:
    var_pattern = re.compile(r"\$\{var::(\w+(\.\w+)*)\}")

    evaluators = policy_dict["evaluators"]  # looking into the evaluators only:

    for i in range(len(evaluators)):
        for key, value in evaluators[i]["provider_args"].items():
            match = check_match(value, var_pattern)
            if bool(match):
                evaluators[i]["provider_args"][key] = get_var(var_dict, match.group(1))

        for key, value in evaluators[i]["condition"].items():
            match = check_match(value, var_pattern)
            if bool(match):
                evaluators[i]["condition"][key] = get_var(var_dict, match.group(1))

    return policy_dict
