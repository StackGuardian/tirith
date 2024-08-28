import re
import pydash


def check_match(string: str, pattern: re.Pattern) -> re.Match:
    match_ = re.fullmatch(pattern, string)
    return match_


def replace_vars(policy_dict: dict, var_dict: dict) -> dict:
    var_pattern = re.compile(r"\$\{var::(\w+(\.\w+)*)\}")

    evaluators = policy_dict["evaluators"]  # looking into the evaluators only:

    for i in range(len(evaluators)):
        for key, value in evaluators[i]["provider_args"].items():
            if isinstance(value, str):
                match = check_match(value, var_pattern)
                if bool(match):
                    evaluators[i]["provider_args"][key] = pydash.get(var_dict, match.group(1))

        for key, value in evaluators[i]["condition"].items():
            if isinstance(value, str):
                match = check_match(value, var_pattern)
                if bool(match):
                    evaluators[i]["condition"][key] = pydash.get(var_dict, match.group(1))

    return policy_dict
