import operator

from functools import reduce
from typing import Callable, Dict, List
from ..common import create_result_dict


def get_value(provider_args: Dict, input_data: Dict) -> Dict:
    # Must be validated first whether the provider args are valid for this op type
    key_path: str = provider_args["key_path"]

    result = reduce(operator.getitem, key_path.split("."), input_data)
    return create_result_dict(value=result, meta=None, err=None)


SUPPORTED_OPS: Dict[str, Callable] = {"get_value": get_value}


def provide(provider_args: Dict, input_data: Dict) -> List[Dict]:
    results = []
    operation_type = provider_args["operation_type"]

    op_handler = SUPPORTED_OPS.get(operation_type)

    if op_handler is None:
        results.append(create_result_dict(err=f"operation_type: {operation_type} is not supported"))
        return results

    result = op_handler(provider_args, input_data)
    results.append(result)
    return results
