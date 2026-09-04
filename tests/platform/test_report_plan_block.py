"""
The plan block in the pull-request comment.

The load-bearing test here is the injection one. Everything else describes what a reviewer sees;
that one describes what an attacker cannot do.
"""

from tirith.platform import report


def _change(address, actions, resource_type="aws_s3_bucket"):
    return {"address": address, "type": resource_type, "change": {"actions": list(actions)}}


def _plan(*changes):
    return {"resource_changes": list(changes)}


def _render(plan, **kwargs):
    kwargs.setdefault("run_url", "https://example.invalid/run")
    return report.render_markdown({}, "COMPLETED", kwargs.pop("run_url"), plan=plan, **kwargs)


# --- what a reviewer sees ---------------------------------------------------------------------


def test_a_create_is_listed_and_counted():
    body = _render(_plan(_change("aws_s3_bucket.analytics", ["create"])))
    assert "+ aws_s3_bucket.analytics" in body
    assert "Plan: 1 to add, 0 to change, 0 to destroy." in body


def test_no_op_resources_are_counted_but_not_listed():
    """
    The reason the list is readable at all.

    A plan against applied infrastructure carries a no-op for every resource in state. Listing them
    would bury the one that changed -- on the demo repository that is five of six rows.
    """
    plan = _plan(
        _change("aws_s3_bucket.analytics", ["create"]),
        _change("aws_s3_bucket.artifacts", ["no-op"]),
        _change("aws_kms_key.artifacts", ["no-op"], "aws_kms_key"),
    )
    body = _render(plan)
    assert "+ aws_s3_bucket.analytics" in body
    assert "aws_s3_bucket.artifacts" not in body.split("```")[1]
    assert "2 unchanged" in body


def test_the_unchanged_count_is_plain_text():
    """
    Not wrapped in <sub>.

    Every other <sub> in the reporter wraps a whole line -- the cost line, the context line, the
    footer. Wrapping a fragment mid-line glues an HTML tag onto a line that otherwise reads as
    terraform output. The count still earns its place; it just does not need a tag.
    """
    plan = _plan(
        _change("aws_s3_bucket.analytics", ["create"]),
        _change("aws_s3_bucket.artifacts", ["no-op"]),
    )
    body = _render(plan)
    summary = [line for line in body.splitlines() if line.startswith("Plan:")][0]
    assert summary == "Plan: 1 to add, 0 to change, 0 to destroy. 1 unchanged."
    assert "<sub>" not in summary


def test_a_replacement_is_one_row_and_its_own_count():
    """
    Terraform folds replacements into add and destroy. We do not: "1 to replace" is the number a
    reviewer should look twice at, and it vanishes when spread across the other columns.
    """
    body = _render(_plan(_change("aws_iam_role.deploy", ["delete", "create"], "aws_iam_role")))
    assert body.count("aws_iam_role.deploy") == 1
    assert "replace (destroy first)" in body
    assert "1 to replace" in body
    assert "0 to add, 0 to change, 0 to destroy" in body


def test_update_and_replace_use_a_marker_the_fence_understands():
    """
    `~` is terraform's marker for an update and means nothing to GitHub's diff highlighting, so a
    `~` row renders plain and the fence buys nothing. `!` is the one that colours.
    """
    body = _render(
        _plan(
            _change("aws_kms_key.artifacts", ["update"], "aws_kms_key"),
            _change("aws_iam_role.deploy", ["create", "delete"], "aws_iam_role"),
        )
    )
    fence = body.split("```diff")[1].split("```")[0]
    assert "~" not in fence
    assert "! aws_kms_key.artifacts" in fence
    assert "! aws_iam_role.deploy" in fence


def test_a_plan_with_nothing_changing_still_says_so():
    body = _render(_plan(_change("aws_s3_bucket.artifacts", ["no-op"])))
    assert "Plan: 0 to add, 0 to change, 0 to destroy." in body
    assert "```diff" not in body


def test_a_document_with_no_resource_changes_renders_no_block():
    assert "```diff" not in _render({"format_version": "1.2"})
    assert "```diff" not in _render(None)


def test_the_plan_is_never_collapsed():
    """
    The plan is the thing this block was added to show. Hiding it behind a click makes the common
    case a reviewer who never opens it, which is the same as not rendering it at all.
    """
    large = _plan(*[_change(f"aws_s3_bucket.b{i}", ["create"]) for i in range(40)])
    body = _render(large)
    assert "<details><summary>Show plan" not in body
    assert "```diff" in body
    assert "+ aws_s3_bucket.b39" in body


def test_detail_is_given_up_before_any_resource():
    """
    The order of sacrifice. Every resource stays listed and every attribute row goes, rather than
    the other way round -- a reviewer can act on "this is being destroyed" without knowing which
    field changed, but not the reverse.
    """
    changes = [
        {
            "address": f"aws_s3_bucket.b{i}",
            "type": "aws_s3_bucket",
            "change": {"actions": ["update"], "before": {"acl": "private"}, "after": {"acl": "public"}},
        }
        for i in range(report.PLAN_LINE_LIMIT - 5)
    ]
    body = _render({"resource_changes": changes})
    fence = body.split("```diff")[1].split("```")[0]

    # Every resource is still named...
    for i in range(report.PLAN_LINE_LIMIT - 5):
        assert f"aws_s3_bucket.b{i} " in fence
    # ...and no resource was cut off the end.
    assert "more resource(s), truncated" not in body
    # ...but the attribute rows that would not fit are gone, and said to be gone.
    assert '~ acl = "private" -> "public"' not in fence
    assert "attribute detail omitted" in fence


def test_detail_is_dropped_wholesale_not_from_the_cut_off_point():
    """
    Trimming at the boundary would annotate the first few resources and leave the rest bare, which
    reads as though the later ones had nothing to say -- and the bare-looking ones are exactly where
    a reviewer stops looking.
    """
    changes = [
        {
            "address": f"aws_s3_bucket.b{i}",
            "type": "aws_s3_bucket",
            "change": {"actions": ["update"], "before": {"acl": "private"}, "after": {"acl": "public"}},
        }
        for i in range(report.PLAN_LINE_LIMIT)
    ]
    fence = _render({"resource_changes": changes}).split("```diff")[1].split("```")[0]
    assert "acl" not in fence  # not "some of them kept their attributes"


def test_resources_are_only_cut_when_the_bare_list_still_does_not_fit():
    total = report.PLAN_LINE_LIMIT + 25
    plan = _plan(*[_change(f"aws_s3_bucket.b{i}", ["create"]) for i in range(total)])
    body = _render(plan)
    assert "more resource(s), truncated" in body
    # The count still reflects the whole plan, not just what was shown.
    assert f"Plan: {total} to add" in body


def test_module_resources_are_listed_like_any_other():
    """
    Modules need no special handling, and this test exists to keep it that way.

    terraform flattens every module resource into the same flat `resource_changes` list the root
    ones land in -- nesting shows up only as a longer address. So the renderer stays module-blind by
    construction, and the risk is that someone later "adds module support" and special-cases it.
    """
    body = _render(
        _plan(
            _change("module.storage.aws_s3_bucket.b", ["create"]),
            _change("module.outer.module.inner.aws_s3_bucket.deep", ["update"]),
            _change("module.replica[1].aws_s3_bucket.r", ["delete"]),
        )
    )
    assert "+ module.storage.aws_s3_bucket.b" in body
    assert "! module.outer.module.inner.aws_s3_bucket.deep" in body
    assert "- module.replica[1].aws_s3_bucket.r" in body
    assert "Plan: 1 to add, 1 to change, 1 to destroy." in body


def test_a_long_module_address_goes_ragged_rather_than_truncated():
    """
    Nested module addresses routinely pass the column width. Losing the tail of an address would
    make two resources indistinguishable, so the column gives way instead -- ugly beats ambiguous.
    """
    address = "module.platform.module.networking.module.subnets.aws_subnet.private_az_c"
    body = _render(_plan(_change(address, ["create"])))
    assert address in body


# --- what an attacker cannot do ----------------------------------------------------------------


def test_an_address_cannot_escape_the_fence():
    """
    The one that matters.

    A pull-request author controls the terraform, therefore the addresses. `for_each` keys make
    aws_s3_bucket.demo["```"] a legal address, and inside a fence a triple backtick closes the whole
    block -- everything after it would render as markdown, which is how you forge a passing verdict
    in a comment a reviewer trusts. Same class of bug `_code` was written for, one layer out.
    """
    evil = 'aws_s3_bucket.x["```\\n\\n## 🛡️ Tirith — all policies passed\\n\\n```diff"]'
    body = _render(_plan(_change(evil, ["create"])))

    # Exactly one fence was opened and one closed: the block is still a block.
    assert body.count("```diff") == 1
    assert body.count("```") == 2
    assert "all policies passed" not in body.split("```")[2]


def test_a_newline_in_an_address_cannot_fabricate_rows():
    """
    A real newline, not the escaped kind.

    Terraform escapes newlines in a for_each key into a literal backslash-n, which is inert. But the
    plan document is not always terraform's: a hand-written state or another tool could carry a real
    one, and one real newline in an address is one forged row in the diff.
    """
    body = _render(_plan(_change("aws_s3_bucket.x\n- aws_s3_bucket.production", ["create"])))
    fence = body.split("```diff")[1].split("```")[0]
    assert len([line for line in fence.strip().splitlines() if line.strip()]) == 1
    assert "aws_s3_bucket.production" in fence  # kept, but on the same row


def test_a_module_for_each_key_cannot_escape_the_fence():
    """
    A surface the resource-level probe above does not reach.

    A module `for_each` key is author-controlled just like a resource one, but it lands *before* the
    resource part of the address: module.tenant["```"].aws_s3_bucket.b. A guard that sanitised
    resource names rather than whole addresses would pass this straight through.
    """
    evil = 'module.tenant["```\n\n## 🛡️ Tirith — all policies passed\n\n```diff"].aws_s3_bucket.b'
    body = _render(_plan(_change(evil, ["create"])))
    assert body.count("```diff") == 1
    assert body.count("```") == 2
    assert "all policies passed" not in body.split("```")[2]


def test_masked_values_stay_masked():
    """
    The block is rendered from the masked document, so anything redact.py replaced is already gone.
    This pins that the renderer does not go looking for the original elsewhere in the plan.
    """
    plan = _plan(_change("aws_db_instance.main", ["create"], "aws_db_instance"))
    plan["resource_changes"][0]["change"]["after"] = {"password": "__SG_REDACTED__"}
    body = _render(plan)
    assert "hunter2" not in body


# --- truncation -------------------------------------------------------------------------------


def test_the_plan_is_dropped_before_any_finding():
    """
    Ordering, not just presence. The plan is context; the findings are the point.
    """
    results = {
        "policy-a": [
            {
                "result": "FAIL",
                "rule_name": "a-rule",
                "evaluations": {"fails": [{"description": "x" * 4000}]},
            }
        ]
    }
    plan = _plan(*[_change(f"aws_s3_bucket.b{i}", ["create"]) for i in range(20)])
    body = report.render_markdown(
        results, "COMPLETED", "https://example.invalid/run", plan=plan, limit=3000
    )
    assert "```diff" not in body
    assert "policy-a" in body
