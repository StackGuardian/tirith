import pydash

from typing import Dict


def create_result_dict(value=None, meta=None, err=None) -> Dict:
    return dict(value=value, meta=meta, err=err)


class PydashPathNotFound:
    pass


def _get_path_value_from_dict_internal(splitted_paths, input_data, place_none_if_not_found=False):

    if not splitted_paths:
        return [input_data] if input_data is not PydashPathNotFound else ([None] if place_none_if_not_found else [])

    final_data = []
    expression = splitted_paths[0]
    remaining_paths = splitted_paths[1:]

    # Handle wildcard at the beginning (e.g., "*.something")
    if expression == "":
        if isinstance(input_data, list):
            for item in input_data:
                if remaining_paths:
                    results = _get_path_value_from_dict_internal(remaining_paths, item, place_none_if_not_found)
                    final_data.extend(results)
                else:
                    final_data.append(item)
        elif isinstance(input_data, dict):
            for value in input_data.values():
                if remaining_paths:
                    results = _get_path_value_from_dict_internal(remaining_paths, value, place_none_if_not_found)
                    final_data.extend(results)
                else:
                    final_data.append(value)
        else:
            # For primitive values with empty expression (wildcard match)
            # Just return the value if no more paths to traverse
            if not remaining_paths:
                final_data.append(input_data)
        return final_data

    # Get the value at the current path
    intermediate_val = pydash.get(input_data, expression, default=PydashPathNotFound)

    if intermediate_val is PydashPathNotFound:
        return [None] if place_none_if_not_found else []

    # If there are more paths to traverse
    if remaining_paths:
        if isinstance(intermediate_val, list) and remaining_paths[0] == "":
            # For lists with a wildcard marker, iterate over list items
            # Skip the wildcard marker since iteration is implicit for lists
            paths_to_apply = remaining_paths[1:]
            for val in intermediate_val:
                results = _get_path_value_from_dict_internal(paths_to_apply, val, place_none_if_not_found)
                final_data.extend(results)
        elif isinstance(intermediate_val, dict) and remaining_paths[0] == "":
            # If it's a dict and next path is a wildcard, iterate over dict values
            # Skip the wildcard marker and apply remaining paths to each value
            for value in intermediate_val.values():
                results = _get_path_value_from_dict_internal(remaining_paths[1:], value, place_none_if_not_found)
                final_data.extend(results)
        else:
            # For non-wildcard paths, continue traversal without iteration
            results = _get_path_value_from_dict_internal(remaining_paths, intermediate_val, place_none_if_not_found)
            final_data.extend(results)
    else:
        # This is the final path segment
        final_data.append(intermediate_val)

    return final_data


def get_path_value_from_dict(key_path: str, input_dict: dict, place_none_if_not_found: bool = False):
    """
    Retrieve values from a nested dictionary using a path expression with wildcard support.

    :param key_path: A dot-separated path to traverse the dictionary.
                     Use ``*.`` for wildcards to match all items at that level.
    :type key_path: str
    :param input_dict: The input dictionary to search through.
    :type input_dict: dict
    :param place_none_if_not_found: If True, returns [None] when a path is not found.
                                    If False, returns an empty list []. Defaults to False.
    :type place_none_if_not_found: bool
    :return: A list of values found at the specified path. Returns empty list or [None] if path not found,
             depending on place_none_if_not_found parameter.
    :rtype: list

    **Examples:**

    Basic path traversal::

        >>> data = {"user": {"name": "Alice", "age": 30}}
        >>> get_path_value_from_dict("user.name", data)
        ["Alice"]

    Wildcard with list items::

        >>> data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        >>> get_path_value_from_dict("users.*.name", data)
        ["Alice", "Bob"]

    Wildcard with dictionary values::

        >>> data = {"countries": {"US": {"capital": "Washington"}, "UK": {"capital": "London"}}}
        >>> get_path_value_from_dict("countries.*.capital", data)
        ["Washington", "London"]

    Leading wildcard::

        >>> data = [{"name": "Alice"}, {"name": "Bob"}]
        >>> get_path_value_from_dict("*.name", data)
        ["Alice", "Bob"]

    Path not found behavior::

        >>> data = {"user": {"name": "Alice"}}
        >>> get_path_value_from_dict("missing.path", data)
        []
        >>> get_path_value_from_dict("missing.path", data, place_none_if_not_found=True)
        [None]
    """
    # Handle empty path - return the input data as is
    if not key_path:
        return [input_dict]

    # Split the path by dots and replace '*' with empty string to mark wildcards
    # Empty strings act as markers to iterate over collections (lists or dict values)
    # Example: "users.*.name" -> ["users", "", "name"]
    #          "*.name" -> ["", "name"]
    #          "numbers.*" -> ["numbers", ""]
    splitted_attribute = key_path.split(".")
    splitted_attribute = ["" if part == "*" else part for part in splitted_attribute]

    return _get_path_value_from_dict_internal(splitted_attribute, input_dict, place_none_if_not_found)


class ProviderError:
    """
    A class to represent an error happening in a provider
    """

    def __init__(self, severity_value: int) -> None:
        self.severity_value = severity_value
