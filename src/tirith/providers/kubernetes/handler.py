from typing import Callable, Dict, List

import pydash

from ..common import ProviderError, create_result_dict


class PydashPathNotFound:
    pass


def get_path_value_from_dict(key_path, input_dict):
    # TODO: Make this function more general and then move it to common.py
    splitted_attribute = key_path.split(".*.")
    return _get_path_value_from_dict(splitted_attribute, input_dict)


def _get_path_value_from_dict(splitted_paths, input_dict):
    final_data = []
    expression = splitted_paths[0]
    is_the_last_expression = len(splitted_paths) == 1

    intermediate_val = pydash.get(input_dict, expression, default=PydashPathNotFound)
    if isinstance(intermediate_val, list) and not is_the_last_expression:
        for val in intermediate_val:
            final_attributes = _get_path_value_from_dict(splitted_paths[1:], val)
            for final_attribute in final_attributes:
                final_data.append(final_attribute)
    elif intermediate_val is PydashPathNotFound:
        final_data.append(None)
    elif is_the_last_expression:
        final_data.append(intermediate_val)
    elif ".*" in expression:
        intermediate_exp = expression.split(".*")
        intermediate_data = pydash.get(input_dict, intermediate_exp[0], default=PydashPathNotFound)
        if intermediate_data is not PydashPathNotFound and isinstance(intermediate_data, list):
            for val in intermediate_data:
                final_data.append(val)
    return final_data


def get_value(provider_args: Dict, input_data: Dict, outputs: list) -> Dict:
    # Must be validated first whether the provider args are valid for this op type
    target_kind: str = provider_args.get("kubernetes_kind")
    attribute_path: str = provider_args.get("attribute_path", "")

    if target_kind is None:
        return create_result_dict(value=ProviderError(severity_value=99), err="kubernetes_kind must be provided")
    if attribute_path == "":
        return create_result_dict(value=ProviderError(severity_value=99), err="attribute_path must be provided")

    kubernetes_resources = input_data["yamls"]
    is_kind_found = False

    for resource in kubernetes_resources:
        if resource["kind"] != target_kind:
            continue
        is_kind_found = True
        values = get_path_value_from_dict(attribute_path, resource)
        if ".*." not in attribute_path:
            # If there's no * in the attribute path, the values always have 1 member
            values = values[0]
        outputs.append(create_result_dict(value=values))

    if not is_kind_found:
        outputs.append(
            create_result_dict(value=ProviderError(severity_value=1), err=f"kind: {target_kind} is not found")
        )

    return outputs


SUPPORTED_OPS: Dict[str, Callable] = {"attribute": get_value}


def provide(provider_args: Dict, input_data: Dict) -> List[Dict]:
    results = []
    operation_type = provider_args["operation_type"]

    op_handler = SUPPORTED_OPS.get(operation_type)

    if op_handler is None:
        results.append(create_result_dict(err=f"operation_type: {operation_type} is not supported"))
        return results

    op_handler(provider_args, input_data, results)
    return results
