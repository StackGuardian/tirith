from typing import Dict


def create_result_dict(value=None, meta=None, err=None) -> Dict:
    return dict(value=value, meta=meta, err=err)


class ProviderError:
    """
    A class to represent an error happening in a provider
    """

    def __init__(self, severity_value: int) -> None:
        self.severity_value = severity_value
