from typing import Dict


def create_result_dict(value=None, meta=None, err=None) -> Dict:
    return dict(value=value, meta=meta, err=err)


def get_path_value_from_dict(key_path: str, input_dict: dict, get_path_value_from_dict_func):
    splitted_attribute = key_path.split(".*.")
    return get_path_value_from_dict_func(splitted_attribute, input_dict)


class ProviderError:
    """
    A class to represent an error happening in a provider
    """

    def __init__(self, severity_value: int) -> None:
        self.severity_value = severity_value
