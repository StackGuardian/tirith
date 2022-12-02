import pydash

from typing import Callable, Dict, List
from ..common import create_result_dict


class PydashPathNotFound:
    pass


def get_path_value_from_dict(key_path, input_dict):
    # TODO: Make this function more general and then move it to common.py
    splitted_attribute = key_path.split(".*.")
    return _get_path_value_from_dict(splitted_attribute, input_dict)


def _get_path_value_from_dict(splitted_paths, input_dict):
    final_data = []
    for i, expression in enumerate(splitted_paths):
        intermediate_val = pydash.get(input_dict, expression, default=PydashPathNotFound)
        if isinstance(intermediate_val, list) and i < len(splitted_paths) - 1:
            for val in intermediate_val:
                final_attributes = _get_path_value_from_dict(splitted_paths[1:], val)
                for final_attribute in final_attributes:
                    final_data.append(final_attribute)
        elif i == len(splitted_paths) - 1 and intermediate_val is not PydashPathNotFound:
            final_data.append(intermediate_val)
        elif ".*" in expression:
            intermediate_exp = expression.split(".*")
            intermediate_data = pydash.get(input_dict, intermediate_exp[0], default=PydashPathNotFound)
            if intermediate_data is not PydashPathNotFound and isinstance(intermediate_data, list):
                for val in intermediate_data:
                    final_data.append(val)
    return final_data


def get_value(provider_args: Dict, input_data: Dict) -> Dict:
    # Must be validated first whether the provider args are valid for this op type
    key_path: str = provider_args["key_path"]

    result = get_path_value_from_dict(key_path, input_data)
    return create_result_dict(value=result, meta=None, err=None)


SUPPORTED_OPS: Dict[str, Callable] = {"get_value": get_value}


def provide(provider_args: Dict, input_data: Dict) -> List[Dict]:
    results = []
    operation_type = provider_args["operation_type"]

    op_handler = SUPPORTED_OPS.get(operation_type)

    if op_handler is None:
        # TODO: We should think of a mechanism to tell the core that this error message
        # should be marked as yellow so it gets the attention of the user,
        # perhaps by prefixing the error message with `WARN:` or `ERR:`
        results.append(create_result_dict(err=f"operation_type: {operation_type} is not supported"))
        return results

    result = op_handler(provider_args, input_data)
    results.append(result)
    return results
