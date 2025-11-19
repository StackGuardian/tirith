import pydash

from typing import Callable, Dict, List
from ..common import create_result_dict, ProviderError, get_path_value_from_dict


def get_value(provider_args: Dict, input_data: Dict, outputs: list) -> Dict:
    # Must be validated first whether the provider args are valid for this op type
    target_kind: str = provider_args.get("kubernetes_kind")
    attribute_path: str = provider_args.get("attribute_path", "")

    if target_kind is None:
        return create_result_dict(value=ProviderError(severity_value=99), err="kubernetes_kind must be provided")
    if attribute_path == "":
        return create_result_dict(value=ProviderError(severity_value=99), err="attribute_path must be provided")

    kubernetes_resources = input_data
    is_kind_found = False

    for resource in kubernetes_resources:
        if resource["kind"] != target_kind:
            continue
        is_kind_found = True
        values = get_path_value_from_dict(attribute_path, resource, place_none_if_not_found=True)
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
