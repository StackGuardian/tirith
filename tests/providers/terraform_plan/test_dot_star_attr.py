from tirith.providers.terraform_plan import handler
from pytest import mark

checks_passing = [
    (
        "a.*.b.c.*",
        {
            "a": [
                {"b": {"c": ["val1", "val3"]}},
                {"b": {"c": ["val8", "val4"]}},
                {"b": {"c": ["val9", "val5"]}},
                {"d": {"c": ["val10", "val6"]}},
                {"b": {"f": ["val11", "val7"]}},
            ]
        },
        ["val1", "val3", "val8", "val4", "val9", "val5"],
    ),
    (
        "a.*.b.c",
        {
            "a": [
                {"b": {"c": ["val1", "val3"]}},
                {"b": {"c": ["val8", "val4"]}},
                {"b": {"c": ["val9", "val5"]}},
                {"d": {"c": ["val10", "val6"]}},
                {"b": {"f": ["val11", "val7"]}},
            ]
        },
        [["val1", "val3"], ["val8", "val4"], ["val9", "val5"]],
    ),
    (
        "a.b.c",
        {"a": {"b": {"c": ["val1", "val3"]}}},
        [["val1", "val3"]],
    ),
    (
        "a.*.b",
        {
            "a": [
                {"b": {"c": ["val1", "val3"]}},
                {"b": {"c": ["val8", "val4"]}},
                {"b": {"c": ["val9", "val5"]}},
                {"d": {"c": ["val10", "val6"]}},
                {"b": {"f": ["val11", "val7"]}},
            ]
        },
        [{"c": ["val1", "val3"]}, {"c": ["val8", "val4"]}, {"c": ["val9", "val5"]}, {"f": ["val11", "val7"]}],
    ),
]

# pytest -v -m passing
@mark.passing
@mark.parametrize("split_expressions,input_data,expected_result", checks_passing)
def test_(split_expressions, input_data, expected_result):
    result = handler._wrapper_get_exp_attribute(split_expressions, input_data)
    assert result == expected_result
