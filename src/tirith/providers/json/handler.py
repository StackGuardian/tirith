from typing import Callable, Dict, List
from ..common import create_result_dict, ProviderError, get_path_value_from_input


def get_value(provider_args: Dict, input_data: Dict) -> List[dict]:
    # Must be validated first whether the provider args are valid for this op type
    key_path: str = provider_args["key_path"]

    values = get_path_value_from_input(key_path, input_data)

    if len(values) == 0:
        severity_value = 2
        return [
            create_result_dict(
                value=ProviderError(severity_value=severity_value),
                err=f"key_path: `{key_path}` is not found (severity: {severity_value})",
            )
        ]

    outputs = [create_result_dict(value=value, meta=None, err=None) for value in values]

    return outputs


SUPPORTED_OPS: Dict[str, Callable] = {"get_value": get_value}


def provide(provider_args: Dict, input_data: Dict) -> List[Dict]:
    operation_type = provider_args["operation_type"]

    op_handler = SUPPORTED_OPS.get(operation_type)

    if op_handler is None:
        # TODO: We should think of a mechanism to tell the core that this error message
        # should be marked as yellow so it gets the attention of the user,
        # perhaps by prefixing the error message with `WARN:` or `ERR:`
        return [create_result_dict(err=f"operation_type: {operation_type} is not supported")]

    results = op_handler(provider_args, input_data)
    return results
