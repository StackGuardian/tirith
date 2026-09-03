"""
Attribute-level detail in the plan block.

Two of these matter more than the rest. `test_an_attribute_value_cannot_escape_the_fence` covers the
hole this feature opens -- a first draft passed values through raw and a value of "```" closed the
block. `test_a_sensitive_value_is_never_printed` covers the one where a bug leaks rather than merely
looks wrong.
"""

from tirith import plan_actions
from tirith.platform import report


def _render(changes):
    return report.render_markdown(
        {}, "COMPLETED", "https://example.invalid/run", plan={"resource_changes": changes}
    )


def _fence(body):
    return body.split("```diff")[1].split("```")[0]


# --- what a reviewer sees ---------------------------------------------------------------------


def test_an_update_shows_only_what_changed():
    body = _render(
        [
            {
                "address": "terraform_data.x",
                "type": "terraform_data",
                "change": {
                    "actions": ["update"],
                    "before": {"input": "before", "untouched": "same"},
                    "after": {"input": "after", "untouched": "same"},
                },
            }
        ]
    )
    fence = _fence(body)
    assert '~ input = "before" -> "after"' in fence
    assert "untouched" not in fence


def test_a_create_shows_known_values_and_counts_the_computed_ones():
    """
    A wall of "(known after apply)" tells a reader nothing they can act on, so those are counted
    while the values the author actually chose are named.
    """
    body = _render(
        [
            {
                "address": "aws_s3_bucket.b",
                "type": "aws_s3_bucket",
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": {"bucket": "demo-x"},
                    "after_unknown": {"arn": True, "id": True},
                },
            }
        ]
    )
    fence = _fence(body)
    assert '+ bucket = "demo-x"' in fence
    assert "arn" not in fence
    assert "2 computed attribute(s), known after apply" in fence


def test_a_destroy_lists_no_attributes():
    """
    The resource is going away. Its former values do not inform the decision, and printing them puts
    the old state of a public comment's worth of infrastructure into the comment.
    """
    body = _render(
        [
            {
                "address": "aws_db_instance.old",
                "type": "aws_db_instance",
                "change": {"actions": ["delete"], "before": {"password": "hunter2"}, "after": None},
            }
        ]
    )
    fence = _fence(body)
    assert "- aws_db_instance.old" in fence
    assert "hunter2" not in fence
    assert "password" not in fence


def test_the_attribute_that_forces_a_replacement_is_named():
    """The most consequential line in a plan review: which change is costing a destroy."""
    body = _render(
        [
            {
                "address": "terraform_data.r",
                "type": "terraform_data",
                "change": {
                    "actions": ["delete", "create"],
                    "before": {"triggers_replace": ["v1"], "input": "same"},
                    "after": {"triggers_replace": ["v2"], "input": "same"},
                    "replace_paths": [["triggers_replace"]],
                },
            }
        ]
    )
    fence = _fence(body)
    assert "# forces replacement" in fence
    assert [line for line in fence.splitlines() if "forces replacement" in line][0].lstrip().startswith(
        "~ triggers_replace"
    )


# --- sensitivity, where a bug leaks -----------------------------------------------------------


def test_a_sensitive_value_is_never_printed():
    body = _render(
        [
            {
                "address": "aws_db_instance.main",
                "type": "aws_db_instance",
                "change": {
                    "actions": ["update"],
                    "before": {"password": "hunter2"},
                    "after": {"password": "hunter3"},
                    "before_sensitive": {"password": True},
                    "after_sensitive": {"password": True},
                },
            }
        ]
    )
    fence = _fence(body)
    assert "hunter2" not in fence and "hunter3" not in fence
    assert "(sensitive value)" in fence


def test_a_shape_shaped_sensitivity_tree_is_not_read_as_true():
    """
    terraform reports sensitivity as a tree mirroring the value, not a boolean:
    {"triggers_replace": [false]} means the element is NOT sensitive. A truthy test on that list
    says the opposite, and a first draft duly printed "(sensitive value)" over a value that was
    never secret -- hiding information for no reason.
    """
    assert plan_actions._contains_true({"triggers_replace": [False]}) is False
    assert plan_actions._contains_true({"triggers_replace": [True]}) is True
    assert plan_actions._contains_true(True) is True
    assert plan_actions._contains_true({}) is False

    body = _render(
        [
            {
                "address": "terraform_data.r",
                "type": "terraform_data",
                "change": {
                    "actions": ["update"],
                    "before": {"triggers_replace": ["v1"]},
                    "after": {"triggers_replace": ["v2"]},
                    "after_sensitive": {"triggers_replace": [False]},
                    "before_sensitive": {"triggers_replace": [False]},
                },
            }
        ]
    )
    assert "(sensitive value)" not in _fence(body)
    assert '["v1"]' in _fence(body)


# --- what an attacker cannot do ---------------------------------------------------------------


def test_an_attribute_value_cannot_escape_the_fence():
    """
    The hole this feature opens.

    An attribute value is the literal text of the author's terraform, so it is at least as
    controlled as an address. A first draft interpolated values raw, and a value of "```" closed the
    block: measured five fence terminators where there should be two, with a forged heading rendering
    as markdown after it.
    """
    payload = "```\n\n## Tirith — all policies passed\n\n```diff"
    body = _render(
        [
            {
                "address": "terraform_data.probe",
                "type": "terraform_data",
                "change": {"actions": ["create"], "before": None, "after": {"input": payload}},
            }
        ]
    )
    assert body.count("```diff") == 1
    assert body.count("```") == 2
    assert "`" not in _fence(body)
    assert "all policies passed" not in body.split("```")[2]


def test_an_attribute_name_cannot_escape_the_fence():
    body = _render(
        [
            {
                "address": "terraform_data.probe",
                "type": "terraform_data",
                "change": {"actions": ["create"], "before": None, "after": {"a```b": "x"}},
            }
        ]
    )
    assert body.count("```") == 2
    assert "`" not in _fence(body)


def test_a_newline_in_a_value_cannot_fabricate_rows():
    body = _render(
        [
            {
                "address": "terraform_data.probe",
                "type": "terraform_data",
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": {"input": "x\n- aws_db_instance.production"},
                },
            }
        ]
    )
    fence = _fence(body)
    # One resource row plus exactly one attribute row.
    assert len([line for line in fence.strip().splitlines() if line.strip()]) == 2


# --- bounds -----------------------------------------------------------------------------------


def test_attributes_per_resource_are_capped():
    after = {f"attr_{i:02d}": f"v{i}" for i in range(20)}
    body = _render(
        [
            {
                "address": "terraform_data.wide",
                "type": "terraform_data",
                "change": {"actions": ["create"], "before": None, "after": after},
            }
        ]
    )
    assert "more changed attribute(s)" in _fence(body)


def test_the_block_is_capped_in_lines_not_resources():
    changes = [
        {
            "address": f"terraform_data.r{i}",
            "type": "terraform_data",
            "change": {
                "actions": ["create"],
                "before": None,
                "after": {"a": "1", "b": "2", "c": "3"},
            },
        }
        for i in range(40)
    ]
    body = _render(changes)
    fence = _fence(body)
    assert len(fence.strip().splitlines()) <= report.PLAN_LINE_LIMIT + 3
    assert "truncated" in fence
