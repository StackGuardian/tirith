import pytest
from tirith.providers.common import get_path_value_from_dict


# Test data for simple path access
simple_path_cases = [
    ({"user": {"name": "Alice", "age": 30}}, "user.name", ["Alice"]),
    ({"level1": {"level2": {"level3": {"value": "deep"}}}}, "level1.level2.level3.value", ["deep"]),
    ({"name": "Alice", "age": 30}, "name", ["Alice"]),
    ({"items": ["a", "b", "c"]}, "items.0", ["a"]),
    ({"settings": {"enabled": True, "visible": False}}, "settings.enabled", [True]),
    ({"items": {"0": "first", "1": "second"}}, "items.0", ["first"]),
    ({"user-profile": {"first-name": "Alice"}}, "user-profile.first-name", ["Alice"]),
]

# Test data for wildcard with lists
wildcard_list_cases = [
    ({"users": [{"name": "Alice"}, {"name": "Bob"}, {"name": "Charlie"}]}, "users.*.name", ["Alice", "Bob", "Charlie"]),
    ([{"name": "Alice"}, {"name": "Bob"}], "*.name", ["Alice", "Bob"]),
    ({"numbers": [1, 2, 3, 4, 5]}, "numbers.*", [1, 2, 3, 4, 5]),
    ({"items": [{"name": "Alice"}, {"other": "value"}, {"name": "Bob"}]}, "items.*.name", ["Alice", "Bob"]),
]

# Test data for wildcard with dictionaries
wildcard_dict_cases = [
    (
        {"countries": {"US": {"capital": "Washington"}, "UK": {"capital": "London"}, "FR": {"capital": "Paris"}}},
        "countries.*.capital",
        {"Washington", "London", "Paris"},
    ),
    ({"a": {"value": 1}, "b": {"value": 2}, "c": {"value": 3}}, "*.value", {1, 2, 3}),
    ({"mixed": {"a": 1, "b": "string", "c": True, "d": None}}, "mixed.*", {1, "string", True, None}),
]

# Test data for multiple wildcards
multiple_wildcard_cases = [
    (
        {
            "departments": [
                {"name": "Engineering", "employees": [{"name": "Alice"}, {"name": "Bob"}]},
                {"name": "Sales", "employees": [{"name": "Charlie"}, {"name": "Diana"}]},
            ]
        },
        "departments.*.employees.*.name",
        ["Alice", "Bob", "Charlie", "Diana"],
    ),
    ({"groups": [[{"id": 1}, {"id": 2}], [{"id": 3}, {"id": 4}]]}, "groups.*.*.id", [1, 2, 3, 4]),
    ({"a": {"b": [{"c": 1}, {"c": 2}]}, "x": {"b": [{"c": 3}, {"c": 4}]}}, "*.b.*.c", {1, 2, 3, 4}),
]

# Test data for path not found (default behavior)
path_not_found_cases = [
    ({"user": {"name": "Alice"}}, "user.age", []),
    ({"level1": {"level2": {}}}, "level1.level2.level3.value", []),
    ({"users": []}, "users.*.name", []),
    ({"users": {}}, "users.*.name", []),
]

# Test data for path not found with flag
path_not_found_with_flag_cases = [
    ({"user": {"name": "Alice"}}, "user.age", True, [None]),
    ({"level1": {"level2": {}}}, "level1.level2.level3.value", True, [None]),
]

# Test data for special values
special_value_cases = [
    ({"user": {"profile": None}}, "user.profile", [None]),
    ({"key": "value"}, "", [{"key": "value"}]),
]

# Test data for complex nested structures
complex_structure_cases = [
    (
        {
            "organizations": [
                {
                    "name": "Org1",
                    "departments": [
                        {"name": "Dept1", "teams": [{"members": [{"email": "a@test.com"}, {"email": "b@test.com"}]}]}
                    ],
                },
                {"name": "Org2", "departments": [{"name": "Dept2", "teams": [{"members": [{"email": "c@test.com"}]}]}]},
            ]
        },
        "organizations.*.departments.*.teams.*.members.*.email",
        ["a@test.com", "b@test.com", "c@test.com"],
    ),
]


@pytest.mark.parametrize("data,path,expected", simple_path_cases)
def test_simple_path_access(data, path, expected):
    """Test basic path traversal without wildcards"""
    result = get_path_value_from_dict(path, data)
    assert result == expected


@pytest.mark.parametrize("data,path,expected", wildcard_list_cases)
def test_wildcard_with_list(data, path, expected):
    """Test wildcard with list of dictionaries"""
    result = get_path_value_from_dict(path, data)
    assert result == expected


@pytest.mark.parametrize("data,path,expected_set", wildcard_dict_cases)
def test_wildcard_with_dict(data, path, expected_set):
    """Test wildcard with dictionary values (order-independent)"""
    result = get_path_value_from_dict(path, data)
    assert set(result) == expected_set


@pytest.mark.parametrize("data,path,expected", multiple_wildcard_cases)
def test_multiple_wildcards(data, path, expected):
    """Test multiple wildcards in the path"""
    result = get_path_value_from_dict(path, data)
    if isinstance(expected, set):
        assert set(result) == expected
    else:
        assert result == expected


@pytest.mark.parametrize("data,path,expected", path_not_found_cases)
def test_path_not_found_default(data, path, expected):
    """Test that non-existent path returns empty list by default"""
    result = get_path_value_from_dict(path, data)
    assert result == expected


@pytest.mark.parametrize("data,path,flag,expected", path_not_found_with_flag_cases)
def test_path_not_found_with_flag(data, path, flag, expected):
    """Test that non-existent path returns [None] when flag is True"""
    result = get_path_value_from_dict(path, data, place_none_if_not_found=flag)
    assert result == expected


@pytest.mark.parametrize("data,path,expected", special_value_cases)
def test_special_values(data, path, expected):
    """Test handling of special values like None and empty paths"""
    result = get_path_value_from_dict(path, data)
    assert result == expected


@pytest.mark.parametrize("data,path,expected", complex_structure_cases)
def test_complex_nested_structure(data, path, expected):
    """Test complex real-world-like nested structures"""
    result = get_path_value_from_dict(path, data)
    assert result == expected


# Test data for edge cases with wildcards
edge_case_wildcard_cases = [
    # Nested wildcard when intermediate path is missing
    ({"groups": [{"users": [{"name": "Alice"}]}, {"other": "data"}]}, "groups.*.users.*.name", ["Alice"]),
    # Partial match with wildcard - some list items have the key and others don't
    ({"items": [{"name": "Alice"}, {"other": "value"}, {"name": "Bob"}]}, "items.*.name", ["Alice", "Bob"]),
]

# Test data for empty containers
empty_container_cases = [
    ({"users": []}, "users.*.name", False, []),
    ({"users": {}}, "users.*.name", False, []),
]

# Test data for empty containers with flag
empty_container_with_flag_cases = [
    ({"users": []}, "users.*.name", True, []),
    ({"users": {}}, "users.*.name", True, []),
]


@pytest.mark.parametrize("data,path,expected", edge_case_wildcard_cases)
def test_edge_case_wildcards(data, path, expected):
    """Test edge cases with wildcards like missing intermediate paths and partial matches"""
    result = get_path_value_from_dict(path, data)
    assert result == expected


@pytest.mark.parametrize("data,path,flag,expected", empty_container_cases)
def test_empty_containers(data, path, flag, expected):
    """Test empty containers return empty list"""
    result = get_path_value_from_dict(path, data, place_none_if_not_found=flag)
    assert result == expected


@pytest.mark.parametrize("data,path,flag,expected", empty_container_with_flag_cases)
def test_empty_containers_with_flag(data, path, flag, expected):
    """Test empty containers with place_none_if_not_found flag"""
    # Empty containers don't trigger the flag since they exist but are empty
    result = get_path_value_from_dict(path, data, place_none_if_not_found=flag)
    assert result == expected


# Test data for wildcard with no remaining paths
wildcard_list_no_remaining_cases = [
    ([1, 2, 3, 4, 5], "*", [1, 2, 3, 4, 5]),
    (
        [{"name": "Alice"}, {"name": "Bob"}, {"name": "Charlie"}],
        "*",
        [{"name": "Alice"}, {"name": "Bob"}, {"name": "Charlie"}],
    ),
    ({"items": [10, 20, 30]}, "items.*", [10, 20, 30]),
]

# Test data for wildcard dict with no remaining paths
wildcard_dict_no_remaining_cases = [
    ({"a": 1, "b": 2, "c": 3}, "*", {1, 2, 3}),
    ({"config": {"x": 10, "y": 20, "z": 30}}, "config.*", {10, 20, 30}),
    (
        {"config": {"setting1": "value1", "setting2": "value2", "setting3": "value3"}},
        "config.*",
        {"value1", "value2", "value3"},
    ),
    ({"settings": {"enabled": True, "count": 42, "name": "test"}}, "settings.*", {True, 42, "test"}),
    ({"items": {"x": 100, "y": "text", "z": True}}, "items.*", {100, "text", True}),
]

# Test data for wildcard with primitive values
wildcard_primitive_cases = [
    (42, "*", [42]),
    ("hello", "*", ["hello"]),
    (True, "*", [True]),
    (None, "*", [None]),
]


@pytest.mark.parametrize("data,path,expected", wildcard_list_no_remaining_cases)
def test_wildcard_list_no_remaining_paths(data, path, expected):
    """Test wildcard at the end of path with list and no remaining paths - covers lines 31-32"""
    result = get_path_value_from_dict(path, data)
    assert result == expected


@pytest.mark.parametrize("data,path,expected_set", wildcard_dict_no_remaining_cases)
def test_wildcard_dict_no_remaining_paths(data, path, expected_set):
    """Test wildcard at the end of path with dict and no remaining paths - covers lines 38-39"""
    result = get_path_value_from_dict(path, data)
    assert set(result) == expected_set


@pytest.mark.parametrize("data,path,expected", wildcard_primitive_cases)
def test_wildcard_primitive_no_remaining_paths(data, path, expected):
    """Test wildcard applied to primitive value with no remaining paths - covers lines 42-43"""
    result = get_path_value_from_dict(path, data)
    assert result == expected
