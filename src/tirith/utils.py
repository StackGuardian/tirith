import logging
import json

logger = logging.getLogger(__name__)
from typing import Any


def json_format_value(value: Any) -> str:
    """
    Format a Python value as a JSON string representation.

    This produces a more language-agnostic representation of values that's
    suitable for displaying in evaluation messages.

    :param value: Any Python value
    :type value: Any

    :returns: A JSON-formatted string representation of the value, enclosed in backticks
    :rtype: str
    """

    try:
        # For basic types, use JSON representation
        json_str = json.dumps(value)
        return f"`{json_str}`"
    except (TypeError, ValueError):
        # Fall back to string representation for non-JSON-serializable values
        return f"`{str(value)}`"


def sort_collections(inputs):
    try:
        if isinstance(inputs, (str, float, int, bool)):
            return inputs
        elif isinstance(inputs, list):
            if len(inputs) == 0:
                return inputs
            if isinstance(inputs[0], (str, float, int, bool)):
                inputs = sorted(inputs)
                return inputs
            else:
                sorted_list = []
                for index, val in enumerate(inputs):
                    sorted_list.append(sort_collections(val))
                return sorted_list
        elif isinstance(inputs, dict):
            sorted_dict = {}
            for key in inputs:
                sorted_val = sort_collections(inputs[key])
                sorted_dict[key] = sorted_val
            return sorted_dict
        else:
            return inputs
    except Exception as e:
        # TODO: LOG
        logger.exception(e)
        return inputs
