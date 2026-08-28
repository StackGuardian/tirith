import pydash

from typing import Dict, Any, Optional


def create_result_dict(value=None, meta=None, err=None) -> Dict:
    return dict(value=value, meta=meta, err=err)


class PydashPathNotFound:
    pass


def _get_path_value_from_input_internal(splitted_paths, input_data, place_none_if_not_found=False):

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
                    results = _get_path_value_from_input_internal(remaining_paths, item, place_none_if_not_found)
                    final_data.extend(results)
                else:
                    final_data.append(item)
        elif isinstance(input_data, dict):
            for value in input_data.values():
                if remaining_paths:
                    results = _get_path_value_from_input_internal(remaining_paths, value, place_none_if_not_found)
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
                results = _get_path_value_from_input_internal(paths_to_apply, val, place_none_if_not_found)
                final_data.extend(results)
        elif isinstance(intermediate_val, dict) and remaining_paths[0] == "":
            # If it's a dict and next path is a wildcard, iterate over dict values
            # Skip the wildcard marker and apply remaining paths to each value
            for value in intermediate_val.values():
                results = _get_path_value_from_input_internal(remaining_paths[1:], value, place_none_if_not_found)
                final_data.extend(results)
        else:
            # For non-wildcard paths, continue traversal without iteration
            results = _get_path_value_from_input_internal(remaining_paths, intermediate_val, place_none_if_not_found)
            final_data.extend(results)
    else:
        # This is the final path segment
        final_data.append(intermediate_val)

    return final_data


def get_path_value_from_input(key_path: str, input: Any, place_none_if_not_found: bool = False):
    """
    Retrieve values from a nested data structure using a path expression with wildcard support.

    :param key_path: A dot-separated path to traverse the data structure.
                     Use ``*`` for wildcard to match all items at that level.
                     Supports nested structures including dictionaries, lists, and primitives.
    :type key_path: str
    :param input: The input data structure to search through (dict, list, or primitive).
    :type input: Any
    :param place_none_if_not_found: If True, returns [None] when a path is not found.
                                    If False, returns an empty list []. Defaults to False.
    :type place_none_if_not_found: bool
    :return: A list of values found at the specified path. Returns empty list or [None] if path not found,
             depending on place_none_if_not_found parameter.
    :rtype: list

    **Examples:**

    Basic path traversal::

        >>> data = {"user": {"name": "Alice", "age": 30}}
        >>> get_path_value_from_input("user.name", data)
        ["Alice"]

    Wildcard with list items::

        >>> data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        >>> get_path_value_from_input("users.*.name", data)
        ["Alice", "Bob"]

    Wildcard with dictionary values::

        >>> data = {"countries": {"US": {"capital": "Washington"}, "UK": {"capital": "London"}}}
        >>> get_path_value_from_input("countries.*.capital", data)
        ["Washington", "London"]

    Leading wildcard on lists::

        >>> data = [{"name": "Alice"}, {"name": "Bob"}]
        >>> get_path_value_from_input("*.name", data)
        ["Alice", "Bob"]

    Wildcard on primitives::

        >>> get_path_value_from_input("*", 42)
        [42]
        >>> get_path_value_from_input("*", "hello")
        ["hello"]

    Multiple wildcards::

        >>> data = {"groups": [[{"id": 1}, {"id": 2}], [{"id": 3}]]}
        >>> get_path_value_from_input("groups.*.*.id", data)
        [1, 2, 3]

    Empty path returns input as-is::

        >>> data = {"key": "value"}
        >>> get_path_value_from_input("", data)
        [{"key": "value"}]

    Path not found behavior::

        >>> data = {"user": {"name": "Alice"}}
        >>> get_path_value_from_input("missing.path", data)
        []
        >>> get_path_value_from_input("missing.path", data, place_none_if_not_found=True)
        [None]
    """
    # Handle empty path - return the input data as is
    if not key_path:
        return [input]

    # Split the path by dots and replace '*' with empty string to mark wildcards
    # Empty strings act as markers to iterate over collections (lists or dict values)
    # Example: "users.*.name" -> ["users", "", "name"]
    #          "*.name" -> ["", "name"]
    #          "numbers.*" -> ["numbers", ""]
    splitted_attribute = key_path.split(".")
    splitted_attribute = ["" if part == "*" else part for part in splitted_attribute]

    return _get_path_value_from_input_internal(splitted_attribute, input, place_none_if_not_found)


class ProviderError:
    """
    A class to represent an error happening in a provider
    """

    def __init__(self, severity_value: int) -> None:
        self.severity_value = severity_value


def format_context_prefix(context: Optional[Dict]) -> str:
    """
    Render a provider result ``context`` dictionary as a message prefix.

    Providers may attach a ``context`` dictionary to each of their outputs to describe where
    the evaluated value came from. The core prepends the rendered prefix to the evaluator
    message, so that a result reads ``[aws_s3_bucket.example (create)] acl: `"public-read"` is
    not equal to `"private"``` instead of just ```"public-read"` is not equal to `"private"```.

    Recognised keys:

    ``resource_address``
        Address of the resource the value belongs to. Rendered as the bracketed subject.
    ``label``
        Fallback subject when there is no single resource address (for example a resource
        count). Only used when ``resource_address`` is absent.
    ``action``
        Planned action(s) for the resource. Rendered next to the subject.
    ``attribute``
        Name of the attribute being evaluated.

    Any other key is ignored here but is still carried into the result document, so providers
    can supply structured detail without it showing up in the message.

    :param context: The context dictionary attached by the provider, or None
    :type context: Optional[Dict]

    :returns: The prefix to prepend to a message, or an empty string when there is no context
    :rtype: str

    **Examples:**

    >>> format_context_prefix({"resource_address": "aws_vpc.main", "action": "create", "attribute": "cidr_block"})
    '[aws_vpc.main (create)] cidr_block: '
    >>> format_context_prefix({"resource_address": "aws_vpc.main", "attribute": "action"})
    '[aws_vpc.main] action: '
    >>> format_context_prefix({"label": "aws_vpc", "attribute": "count"})
    '[aws_vpc] count: '
    >>> format_context_prefix({"attribute": "terraform_version"})
    'terraform_version: '
    >>> format_context_prefix({"resource_address": "aws_vpc.main", "action": "create"})
    '[aws_vpc.main (create)] '
    >>> format_context_prefix(None)
    ''
    """
    if not context:
        return ""

    subject = context.get("resource_address") or context.get("label")
    action = context.get("action")
    attribute = context.get("attribute")

    subject_prefix = ""
    if subject:
        subject_prefix = "[{} ({})] ".format(subject, action) if action else "[{}] ".format(subject)

    if not attribute:
        # Without an attribute to name, the message that follows reads as a sentence of its
        # own, so the subject is left as a bare lead-in rather than being followed by a colon
        return subject_prefix

    return "{}{}: ".format(subject_prefix, attribute)
