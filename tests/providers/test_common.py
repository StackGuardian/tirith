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


def test_nested_wildcard_with_missing_intermediate():
    """Test nested wildcard when intermediate path is missing"""
    data = {"groups": [{"users": [{"name": "Alice"}]}, {"other": "data"}]}
    result = get_path_value_from_dict("groups.*.users.*.name", data)
    assert result == ["Alice"]


def test_partial_match_with_wildcard():
    """Test when some list items have the key and others don't"""
    data = {"items": [{"name": "Alice"}, {"other": "value"}, {"name": "Bob"}]}
    result = get_path_value_from_dict("items.*.name", data)
    assert result == ["Alice", "Bob"]


def test_empty_containers_default():
    """Test empty containers return empty list"""
    assert get_path_value_from_dict("users.*.name", {"users": []}) == []
    assert get_path_value_from_dict("users.*.name", {"users": {}}) == []


def test_empty_containers_with_flag():
    """Test empty containers with place_none_if_not_found flag"""
    # Empty containers don't trigger the flag since they exist but are empty
    assert get_path_value_from_dict("users.*.name", {"users": []}, place_none_if_not_found=True) == []
    assert get_path_value_from_dict("users.*.name", {"users": {}}, place_none_if_not_found=True) == []


def test_wildcard_with_no_remaining_paths():
    """Test wildcard at the end of path with no remaining paths - covers line 31-32"""
    # Test with list at root level - wildcard with no further paths should return all items
    data = [1, 2, 3, 4, 5]
    result = get_path_value_from_dict("*", data)
    assert result == [1, 2, 3, 4, 5]
    
    # Test with list of dicts - wildcard with no further paths should return all dict items
    data2 = [{"name": "Alice"}, {"name": "Bob"}, {"name": "Charlie"}]
    result2 = get_path_value_from_dict("*", data2)
    assert result2 == [{"name": "Alice"}, {"name": "Bob"}, {"name": "Charlie"}]
    
    # Test with nested list - get list then apply wildcard with no remaining paths
    data3 = {"items": [10, 20, 30]}
    result3 = get_path_value_from_dict("items.*", data3)
    assert result3 == [10, 20, 30]
