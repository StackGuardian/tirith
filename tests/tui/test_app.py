"""
Drive the real app headlessly and assert what it puts on screen.

Textual's `run_test` runs the whole app -- compose, mount, layout, events -- against a virtual
terminal, so these are not widget unit tests: they catch the failures that only appear once
things are actually mounted, which is most of them.

Every test here is skipped when textual is absent, because CI runs the suite on Python 3.8
where it cannot be installed. The rest of the tui test files deliberately avoid importing
textual so they still run there.
"""

import asyncio
import functools
import json
import os
from pathlib import Path

from pytest import fixture, mark, importorskip

importorskip("textual", reason="the TUI is an optional extra (pip install 'py-tirith[tui]')")


def drives_the_app(test):
    """
    Run an async test body under asyncio.

    pytest skips `async def` tests unless an async plugin is installed, and a *skipped* test
    reads as green -- so without this the whole file would appear to pass in CI while
    asserting nothing. Wrapping them keeps the suite's dependencies unchanged (the repo pins
    only pytest and black as dev dependencies) and makes a failure a real failure.
    """

    @functools.wraps(test)
    def wrapper(*args, **kwargs):
        return asyncio.run(test(*args, **kwargs))

    return wrapper


# Imported after the importorskip above, so this module is skipped rather than failing to
# import when textual is absent.
from textual.widgets import Button, Input, Select  # noqa: E402

from tirith.core.core import start_policy_evaluation_from_dict  # noqa: E402
from tirith.tui import examples, results, validate  # noqa: E402
from tirith.tui.app import build_app  # noqa: E402
from tirith.tui.views.builder import BuilderView, parse_value  # noqa: E402
from tirith.tui.views.explorer import ExplorerView  # noqa: E402
from tirith.tui.views.filepicker import DocumentTree, FilePicker  # noqa: E402
from tirith.tui.views.playground import PlaygroundView  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TF_FIXTURES = os.path.join(REPO_ROOT, "tests", "providers", "terraform_plan", "fixtures")
K8S_EXAMPLE_DIR = os.path.join(REPO_ROOT, "src", "tirith", "tui", "examples", "05-kubernetes-probes")

# A wide terminal, so panes are not collapsed to nothing and content is really laid out.
TERMINAL_SIZE = (140, 45)


@fixture
def failing_report():
    """A real evaluation with failures, resource addresses and an attribute diff."""
    example = examples.example_by_key("04-block-destroy")
    return results.parse_report(start_policy_evaluation_from_dict(example.policy, example.input_document))


def _text_of(widget):
    """
    The rendered text of a Static, with markup resolved.

    Textual renamed `Static.renderable` to `.content` (returning a Content rather than a Rich
    renderable), so both are tried -- these tests should not pin the app to one Textual
    version when the app itself works on either.
    """
    content = getattr(widget, "content", None)
    if content is None:
        content = getattr(widget, "renderable", "")
    return content.plain if hasattr(content, "plain") else str(content)


# ------------------------------------------------------------------ explorer


@mark.passing
@drives_the_app
async def test_app_starts_on_explorer_when_given_a_report(failing_report):
    app = build_app(report=failing_report)
    async with app.run_test(size=TERMINAL_SIZE):
        assert app.query_one("#tabs").active == "explorer"


@mark.passing
@drives_the_app
async def test_naming_a_policy_and_input_opens_on_the_results():
    """
    Someone who passed their own policy and plan came to see how it did, so the results are
    what should be on screen -- not the editor they would have to leave to find them.
    """
    example = examples.example_by_key("04-block-destroy")
    app = build_app(policy=example.policy, input_document=example.input_document)

    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()

        assert app.query_one("#tabs").active == "explorer"
        detail = _text_of(app.query_one("#detail-content"))
        assert "aws_db_instance.primary" in detail


@mark.passing
@drives_the_app
async def test_a_policy_without_an_input_stays_on_the_playground():
    """There is nothing to show in the Explorer without a document to evaluate against."""
    example = examples.example_by_key("04-block-destroy")
    app = build_app(policy=example.policy)

    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        assert app.query_one("#tabs").active == "playground"


@mark.passing
@drives_the_app
async def test_app_starts_on_playground_with_no_arguments():
    """With nothing to explore, the useful thing to show is the playground."""
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE):
        assert app.query_one("#tabs").active == "playground"


@mark.passing
@drives_the_app
async def test_explorer_lists_every_check(failing_report):
    app = build_app(report=failing_report)
    async with app.run_test(size=TERMINAL_SIZE):
        tree = app.query_one("#check-tree")
        assert len(tree.root.children) == len(failing_report.checks)


@mark.passing
@drives_the_app
async def test_explorer_opens_on_the_first_failure(failing_report):
    """
    A failing policy is opened to find out what failed, so the detail pane must already be
    showing a failure rather than waiting to be navigated.
    """
    app = build_app(report=failing_report)
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        detail = _text_of(app.query_one("#detail-content"))
        assert "✘" in detail


@mark.passing
@drives_the_app
async def test_explorer_shows_the_resource_address(failing_report):
    """
    The whole reason this view exists: name the resource, which the pretty printer cannot.
    """
    app = build_app(report=failing_report)
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        detail = _text_of(app.query_one("#detail-content"))
        assert "aws_db_instance.primary" in detail


@mark.passing
@drives_the_app
async def test_explorer_shows_the_attribute_that_forced_a_replacement(failing_report):
    """
    The detail that makes a destroy comprehensible: *why* terraform is replacing it.
    """
    app = build_app(report=failing_report)
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        detail = _text_of(app.query_one("#detail-content"))
        assert "instance_class" in detail
        assert "db.t3.medium" in detail and "db.t3.large" in detail


@mark.passing
@drives_the_app
async def test_explorer_names_the_replacement_ordering(failing_report):
    """destroy-first means downtime; it must not read the same as create-first."""
    app = build_app(report=failing_report)
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        assert "destroy first" in _text_of(app.query_one("#detail-content"))


@mark.passing
@drives_the_app
async def test_explorer_accepts_a_report_before_it_has_mounted(failing_report):
    """
    The Playground evaluates while mounting and hands its result to the Explorer, and the two
    mount in an order Textual does not guarantee. This arrived before #report-summary existed
    roughly one run in six, raising NoMatches out of a tab the user had not opened.

    Called directly on an unmounted view, which is the failing order made deterministic. It
    must keep the report rather than raise, and show it once mounted.
    """
    view = ExplorerView(id="unmounted-explorer")
    view.refresh_report(failing_report)

    assert view._report is failing_report


@mark.passing
@drives_the_app
async def test_explorer_handles_an_empty_report():
    """Opening with nothing must not crash the view."""
    app = build_app(report=results.parse_report({}))
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        assert app.query_one("#check-tree").root.label
        assert _text_of(app.query_one("#detail-content"))


@mark.passing
@drives_the_app
async def test_explorer_survives_a_result_document_with_no_meta():
    """infracost sets meta to None; the detail pane must still render."""
    example = examples.example_by_key("03-cost-ceiling")
    report = results.parse_report(start_policy_evaluation_from_dict(example.policy, example.input_document))

    app = build_app(report=report)
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        assert _text_of(app.query_one("#detail-content"))


# ----------------------------------------------------------------- playground


@mark.passing
@drives_the_app
async def test_playground_loads_an_example_and_evaluates_it():
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        assert app.query_one("#policy-editor").text.strip(), "no policy was loaded"
        assert app.query_one("#input-editor").text.strip(), "no input was loaded"
        # The first example fails by design, so a verdict must already be on screen.
        assert _text_of(app.query_one("#playground-status"))


@mark.passing
@drives_the_app
async def test_playground_reports_broken_json_instead_of_crashing():
    """
    While typing, the buffer is invalid most of the time. That is the normal state here, and
    it must produce a message rather than a traceback.
    """
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        playground = app.query_one("#playground-view", PlaygroundView)
        app.query_one("#policy-editor").text = '{"meta": '
        playground.evaluate_now()
        await pilot.pause()

        assert "Cannot evaluate" in _text_of(app.query_one("#playground-status"))
        assert "valid JSON" in _text_of(app.query_one("#findings-list"))


@mark.passing
@drives_the_app
async def test_playground_reports_an_engine_exception_as_a_finding():
    """
    A single `&` makes the engine raise ValueError. The validator catches it first, but the
    playground must also survive whatever the validator does not see.
    """
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        playground = app.query_one("#playground-view", PlaygroundView)
        app.query_one("#policy-editor").text = json.dumps(
            {
                "meta": {"version": "v1", "required_provider": "stackguardian/json"},
                "evaluators": [
                    {
                        "id": "a",
                        "provider_args": {"operation_type": "get_value", "key_path": "x"},
                        "condition": {"type": "Equals", "value": 1},
                    }
                ],
                "eval_expression": "a & a",
            }
        )
        app.query_one("#input-editor").text = '{"x": 1}'
        playground.evaluate_now()
        await pilot.pause()

        # Reported, not raised. Either the validator's message or the engine's is acceptable.
        assert "&&" in _text_of(app.query_one("#findings-list"))


@mark.passing
@drives_the_app
async def test_playground_reports_a_policy_that_is_valid_json_but_not_an_object():
    """A bare list parses fine and would reach the engine; it must be stopped here."""
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        playground = app.query_one("#playground-view", PlaygroundView)
        app.query_one("#policy-editor").text = "[1, 2, 3]"
        playground.evaluate_now()
        await pilot.pause()

        assert "Cannot evaluate" in _text_of(app.query_one("#playground-status"))


@mark.passing
@drives_the_app
async def test_playground_evaluation_updates_the_explorer():
    """
    The tabs share one evaluation, so a run in the playground is explorable next door without
    saving a file in between.
    """
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        tree = app.query_one("#check-tree")
        assert len(tree.root.children) > 0


@mark.passing
@drives_the_app
async def test_playground_loads_every_bundled_example():
    """Each example must survive being loaded into the editors and evaluated."""
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        playground = app.query_one("#playground-view", PlaygroundView)

        for example in examples.load_examples():
            playground.load_example(example)
            await pilot.pause()
            status = _text_of(app.query_one("#playground-status"))
            assert "Cannot evaluate" not in status, f"{example.key}: {status}"


# -------------------------------------------------------------------- builder


@mark.passing
@drives_the_app
async def test_builder_generates_a_valid_policy():
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        app.query_one("#tabs").active = "builder"
        await pilot.pause()

        builder = app.query_one("#builder-view", BuilderView)
        # Fill the arguments the default operation requires, as a user would.
        app.query_one("#arg-terraform_resource_type").value = "aws_s3_bucket"
        app.query_one("#arg-terraform_resource_attribute").value = "acl"
        app.query_one("#id-input").value = "bucket_is_private"
        app.query_one("#value-input").value = '"private"'
        builder._add_check()
        await pilot.pause()

        policy = builder.build_policy()
        evaluator = policy["evaluators"][0]
        assert evaluator["id"] == "bucket_is_private"
        assert evaluator["provider_args"]["terraform_resource_type"] == "aws_s3_bucket"
        # The value keeps its JSON type rather than becoming the string '"private"'.
        assert evaluator["condition"]["value"] == "private"
        assert policy["eval_expression"] == "bucket_is_private"
        assert "✔" in _text_of(app.query_one("#builder-findings"))


@mark.passing
@drives_the_app
async def test_builder_reports_a_missing_required_argument():
    """
    The form knows which arguments an operation requires, so leaving one out is caught before
    the policy is ever run.
    """
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        app.query_one("#tabs").active = "builder"
        await pilot.pause()

        builder = app.query_one("#builder-view", BuilderView)
        app.query_one("#id-input").value = "incomplete"
        builder._add_check()
        await pilot.pause()

        findings = _text_of(app.query_one("#builder-findings"))
        assert "terraform_resource_type" in findings


@mark.passing
@drives_the_app
async def test_builder_form_follows_the_selected_provider():
    """
    Choosing a provider must replace the argument fields, since no two providers take the
    same ones -- that is the point of generating the form from the schema.
    """
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        app.query_one("#tabs").active = "builder"
        await pilot.pause()

        app.query_one("#provider-select").value = "stackguardian/kubernetes"
        await pilot.pause()

        # kubernetes takes kubernetes_kind and attribute_path, which no other provider does.
        assert app.query_one("#arg-kubernetes_kind")
        assert app.query_one("#arg-attribute_path")


@mark.passing
@drives_the_app
async def test_add_check_refuses_a_check_with_no_arguments():
    """
    An empty form used to be a working button: pressing Add check appended a check with no
    provider_args, so three presses gave three of them and a policy the engine could not run.
    """
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        app.query_one("#tabs").active = "builder"
        await pilot.pause()

        builder = app.query_one("#builder-view", BuilderView)
        builder._add_check()
        await pilot.pause()

        assert builder.build_policy()["evaluators"] == []
        # And it names what is missing rather than failing silently.
        assert "terraform_resource_type" in _text_of(app.query_one("#builder-findings"))


@mark.passing
@drives_the_app
async def test_open_in_playground_refuses_an_unrunnable_policy():
    """
    Handing over an invalid policy dropped the user into the Playground showing "Policy is
    incomplete" and no results -- which reads as a broken button, and leaves them in the wrong
    tab to fix it. Staying put, with the reason, is the more useful answer.
    """
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        app.query_one("#tabs").active = "builder"
        await pilot.pause()

        app.query_one("#send-to-playground", Button).press()
        await pilot.pause()

        assert app.query_one("#tabs").active == "builder"
        assert "Add a check" in _text_of(app.query_one("#builder-findings"))


@mark.passing
@drives_the_app
async def test_builder_sends_its_policy_to_the_playground():
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        app.query_one("#tabs").active = "builder"
        await pilot.pause()

        builder = app.query_one("#builder-view", BuilderView)
        app.query_one("#arg-terraform_resource_type").value = "aws_instance"
        app.query_one("#arg-terraform_resource_attribute").value = "instance_type"
        app.query_one("#id-input").value = "check_one"
        app.query_one("#value-input").value = '"t3.micro"'
        builder._add_check()
        await pilot.pause()

        # Pressed rather than clicked: a click depends on where the layout happens to put the
        # button at this terminal size, which is not what this test is about.
        app.query_one("#send-to-playground", Button).press()
        await pilot.pause()

        assert app.query_one("#tabs").active == "playground"
        assert "check_one" in app.query_one("#policy-editor").text


def _add_check(app, check_id, attribute="tags.costcenter", value="true"):
    """Fill the form and add a check, the way a user would."""
    builder = app.query_one("#builder-view", BuilderView)
    app.query_one("#arg-terraform_resource_type").value = "aws_s3_bucket"
    app.query_one("#arg-terraform_resource_attribute").value = attribute
    app.query_one("#id-input").value = check_id
    app.query_one("#value-input").value = value
    builder._add_check()


@mark.passing
@drives_the_app
async def test_the_expression_defaults_to_all_checks_passing():
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        app.query_one("#tabs").active = "builder"
        await pilot.pause()

        _add_check(app, "first")
        await pilot.pause()
        _add_check(app, "second", attribute="acl")
        await pilot.pause()

        assert app.query_one("#expression-input").value == "first && second"


@mark.passing
@drives_the_app
async def test_a_custom_expression_survives_adding_another_check():
    """
    The expression is the one part of a policy that cannot be derived from the checks, so
    regenerating it after the user has written `a && !b` would discard the only thing they
    could not express any other way.
    """
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        app.query_one("#tabs").active = "builder"
        await pilot.pause()

        _add_check(app, "tagged")
        await pilot.pause()
        _add_check(app, "public", attribute="acl")
        await pilot.pause()

        app.query_one("#expression-input").value = "tagged && !public"
        await pilot.pause()

        _add_check(app, "third", attribute="versioning")
        await pilot.pause()

        builder = app.query_one("#builder-view", BuilderView)
        assert builder.build_policy()["eval_expression"] == "tagged && !public"


@mark.passing
@drives_the_app
async def test_clearing_the_checks_releases_a_custom_expression():
    """It named checks that no longer exist, so keeping it would report every id as undefined."""
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        app.query_one("#tabs").active = "builder"
        await pilot.pause()

        _add_check(app, "only")
        await pilot.pause()
        app.query_one("#expression-input").value = "!only"
        await pilot.pause()

        app.query_one("#clear-checks", Button).press()
        await pilot.pause()

        _add_check(app, "fresh")
        await pilot.pause()

        assert app.query_one("#expression-input").value == "fresh"


@mark.passing
@drives_the_app
async def test_an_or_expression_reaches_the_policy():
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        app.query_one("#tabs").active = "builder"
        await pilot.pause()

        _add_check(app, "a")
        await pilot.pause()
        _add_check(app, "b", attribute="acl")
        await pilot.pause()

        app.query_one("#expression-input").value = "a || b"
        await pilot.pause()

        builder = app.query_one("#builder-view", BuilderView)
        policy = builder.build_policy()
        assert policy["eval_expression"] == "a || b"
        # And it is a policy the engine will accept, not just a string in a box.
        assert not [f for f in validate.check_policy(policy) if f.severity == "error"]


@mark.passing
@drives_the_app
async def test_the_builder_names_the_document_its_provider_expects():
    """Choosing a provider is choosing what you must feed it, so the form says which."""
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        app.query_one("#tabs").active = "builder"
        await pilot.pause()

        assert "terraform plan JSON" in _text_of(app.query_one("#provider-summary"))

        app.query_one("#provider-select").value = "stackguardian/infracost"
        await pilot.pause()

        assert "infracost" in _text_of(app.query_one("#provider-summary")).lower()


@mark.passing
@drives_the_app
async def test_the_playground_labels_the_expected_input_document():
    """
    The commonest way to waste ten minutes is feeding the right JSON to the wrong provider,
    so the label tracks whatever the policy currently declares.
    """
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()

        assert "terraform plan JSON" in _text_of(app.query_one("#input-label"))

        playground = app.query_one("#playground-view", PlaygroundView)
        playground.load_example(examples.example_by_key("05-kubernetes-probes"))
        await pilot.pause()

        assert "Kubernetes" in _text_of(app.query_one("#input-label"))


@mark.passing
@drives_the_app
async def test_loading_a_file_picks_the_slot_from_its_contents():
    """
    A policy is recognisable -- an object with `evaluators` and `meta` -- so a file chosen
    without a stated destination still lands in the right editor.
    """
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        playground = app.query_one("#playground-view", PlaygroundView)

        playground._load_path(os.path.join(K8S_EXAMPLE_DIR, "policy.json"))
        await pilot.pause()

        assert "kubernetes_kind" in app.query_one("#policy-editor").text

        playground._load_path(os.path.join(K8S_EXAMPLE_DIR, "input.json"))
        await pilot.pause()

        assert "livenessProbe" in app.query_one("#input-editor").text


@mark.passing
@drives_the_app
async def test_the_about_notes_start_hidden_and_toggle():
    """
    Worth reading once per example, and permanently in the way of the results after that.
    """
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()

        assert not app.query_one("#about-scroll").display

        app.query_one("#toggle-about", Button).press()
        await pilot.pause()
        assert app.query_one("#about-scroll").display

        app.query_one("#toggle-about", Button).press()
        await pilot.pause()
        assert not app.query_one("#about-scroll").display


@mark.passing
@drives_the_app
async def test_clearing_an_editor_empties_it_without_crashing():
    """Clearing leaves the policy unevaluatable, which must report rather than raise."""
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()

        app.query_one("#clear-policy", Button).press()
        await pilot.pause()

        assert app.query_one("#policy-editor").text == ""
        assert "Cannot evaluate" in _text_of(app.query_one("#playground-status"))


@mark.passing
@drives_the_app
async def test_copy_reports_what_it_sent():
    """
    The clipboard goes out as a terminal escape with no reply, so the message says what was
    attempted rather than claiming it landed.
    """
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()

        app.query_one("#copy-policy", Button).press()
        await pilot.pause()

        assert "clipboard" in _text_of(app.query_one("#playground-notice"))


@mark.passing
@drives_the_app
async def test_copying_an_empty_editor_says_so():
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()

        app.query_one("#clear-input", Button).press()
        await pilot.pause()
        app.query_one("#copy-input", Button).press()
        await pilot.pause()

        assert "empty" in _text_of(app.query_one("#playground-notice"))


@mark.passing
@drives_the_app
async def test_open_shows_the_file_browser():
    """Open puts a browser on screen rather than asking the user to know the path already."""
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()

        app.query_one("#open-input", Button).press()
        await pilot.pause()

        picker = app.screen
        assert isinstance(picker, FilePicker)
        # Titled with the destination, so it is clear which editor is about to be filled.
        assert "input" in _text_of(picker.query_one("#file-picker-title"))


@mark.passing
@drives_the_app
async def test_the_browser_lists_documents_and_hides_the_noise():
    """
    Only files the engine can read, and none of the directories that are always huge and
    never interesting from a project root.
    """
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        app.query_one("#open-policy", Button).press()
        await pilot.pause()

        tree = app.screen.query_one("#file-picker-tree", DocumentTree)
        candidates = [
            Path(REPO_ROOT) / "README.md",  # wrong suffix
            Path(REPO_ROOT) / ".git",  # hidden
            Path(REPO_ROOT) / "venv",  # skipped by name
            Path(K8S_EXAMPLE_DIR) / "policy.json",  # kept
        ]
        kept = {p.name for p in tree.filter_paths(candidates)}

        assert kept == {"policy.json"}


@mark.passing
@drives_the_app
async def test_choosing_a_file_loads_it_into_the_editor_that_asked():
    """
    Open on the input editor then choosing a *policy* file still fills the input editor: the
    button named the destination, so the file's contents do not get to override it.
    """
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()

        app.query_one("#open-input", Button).press()
        await pilot.pause()

        app.screen.dismiss(os.path.join(K8S_EXAMPLE_DIR, "policy.json"))
        await pilot.pause()

        assert "kubernetes_kind" in app.query_one("#input-editor").text
        assert "Loaded" in _text_of(app.query_one("#playground-notice"))


@mark.passing
@drives_the_app
async def test_the_browser_can_leave_the_directory_it_opened_in():
    """
    A DirectoryTree only descends from its root, so without re-rooting the picker could reach
    nothing outside the working directory -- and the plan you want to check is usually in
    another repo entirely.
    """
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        app.query_one("#open-policy", Button).press()
        await pilot.pause()

        picker = app.screen
        started_at = picker._directory

        await pilot.press("left")
        await pilot.pause()

        assert picker._directory == os.path.dirname(started_at)
        # The tree really moved, and the header says where to.
        assert str(picker.query_one("#file-picker-tree").path) == picker._directory
        assert picker._directory in _text_of(picker.query_one("#file-picker-location"))


@mark.passing
@drives_the_app
async def test_left_and_right_are_inverses():
    """
    Right descends into the highlighted directory, left returns to the parent -- the pair a
    file manager gives you, so walking in and back out lands where you began.
    """
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        app.query_one("#open-policy", Button).press()
        await pilot.pause()

        picker = app.screen
        started_at = picker._directory

        # Onto the first child directory, then into it.
        await pilot.press("down")
        await pilot.pause()
        await pilot.press("right")
        await pilot.pause()

        assert picker._directory != started_at
        assert os.path.dirname(picker._directory) == started_at

        await pilot.press("left")
        await pilot.pause()

        assert picker._directory == started_at


@mark.passing
@drives_the_app
async def test_right_on_a_file_does_not_navigate():
    """Only directories are somewhere to go; a file is chosen with Enter."""
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        app.query_one("#open-policy", Button).press()
        await pilot.pause()

        picker = app.screen
        picker._show_directory(K8S_EXAMPLE_DIR)
        await pilot.pause()

        # Down onto a file (this directory holds only files), then try to descend.
        await pilot.press("down")
        await pilot.pause()
        await pilot.press("right")
        await pilot.pause()

        assert picker._directory == K8S_EXAMPLE_DIR
        assert isinstance(app.screen, FilePicker)


@mark.passing
@drives_the_app
async def test_going_up_stops_at_the_filesystem_root():
    """`dirname("/")` is `/`, so the guard has to stop rather than loop."""
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        app.query_one("#open-policy", Button).press()
        await pilot.pause()

        picker = app.screen
        for _ in range(12):
            picker.action_go_up()
        await pilot.pause()

        assert picker._directory == os.path.abspath(os.sep)


@mark.passing
@drives_the_app
async def test_typing_a_directory_navigates_rather_than_loading_it():
    """A directory is somewhere to go, not a document to open."""
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        app.query_one("#open-policy", Button).press()
        await pilot.pause()

        picker = app.screen
        field = picker.query_one("#file-picker-path", Input)
        # Focused first: Enter goes to whatever has focus, which is the tree until the user
        # clicks into the path box.
        field.focus()
        await pilot.pause()
        field.value = K8S_EXAMPLE_DIR
        await pilot.press("enter")
        await pilot.pause()

        # Still open, now showing that directory, rather than dismissed with it as a "file".
        assert isinstance(app.screen, FilePicker)
        assert picker._directory == K8S_EXAMPLE_DIR


@mark.passing
@drives_the_app
async def test_cancelling_the_browser_changes_nothing():
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        before = app.query_one("#input-editor").text

        app.query_one("#open-input", Button).press()
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

        assert app.query_one("#input-editor").text == before
        assert not isinstance(app.screen, FilePicker)


@mark.passing
@drives_the_app
async def test_choosing_an_example_from_the_dropdown_loads_it():
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()

        keys = [e.key for e in examples.load_examples()]
        target = keys.index("03-cost-ceiling")
        app.query_one("#example-select", Select).value = target
        await pilot.pause()

        assert "infracost" in app.query_one("#policy-editor").text


@mark.passing
@drives_the_app
async def test_choosing_the_prompt_row_clears_both_editors():
    """
    Picking the prompt means "none of these", so it empties both documents rather than doing
    nothing and leaving the previous example loaded.

    This crashed the app: the guard tested `Select.BLANK`, which is the literal False, while
    the unselected value is the `Select.NULL` sentinel -- so it fell through to int() and
    raised TypeError the first time anyone opened the dropdown and chose the prompt.
    """
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        assert app.query_one("#policy-editor").text.strip()

        app.query_one("#example-select", Select).value = Select.NULL
        await pilot.pause()

        assert app.query_one("#policy-editor").text == ""
        assert app.query_one("#input-editor").text == ""
        # And it reports rather than raising, since an empty policy cannot be evaluated.
        assert "Cannot evaluate" in _text_of(app.query_one("#playground-status"))


@mark.passing
@drives_the_app
async def test_an_unset_optional_argument_is_left_out_of_the_policy():
    """
    Same sentinel confusion in the Builder: an untouched Select would serialise `Select.NULL`
    into the policy as the argument's value instead of being omitted.

    Uses `attribute`, whose exclude_resource_types is genuinely optional -- the required ones
    have to be filled or the check is refused, which is a different rule being tested
    elsewhere.
    """
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        app.query_one("#tabs").active = "builder"
        await pilot.pause()

        builder = app.query_one("#builder-view", BuilderView)
        app.query_one("#arg-terraform_resource_type").value = "*"
        app.query_one("#arg-terraform_resource_attribute").value = "tags.costcenter"
        app.query_one("#id-input").value = "tagged"
        app.query_one("#value-input").value = "true"
        builder._add_check()
        await pilot.pause()

        provider_args = builder.build_policy()["evaluators"][0]["provider_args"]
        assert "exclude_resource_types" not in provider_args, provider_args
        assert "NULL" not in json.dumps(provider_args)


@mark.passing
@drives_the_app
async def test_loading_a_missing_file_reports_rather_than_crashes():
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        playground = app.query_one("#playground-view", PlaygroundView)

        playground._load_path("/no/such/plan.json")
        await pilot.pause()

        assert "No such file" in _text_of(app.query_one("#findings-list"))


@mark.passing
@drives_the_app
async def test_loading_a_file_of_broken_json_names_the_position(tmp_path):
    broken = tmp_path / "broken.json"
    broken.write_text('{"resource_changes": [')

    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        playground = app.query_one("#playground-view", PlaygroundView)

        playground._load_path(str(broken))
        await pilot.pause()

        findings = _text_of(app.query_one("#findings-list"))
        assert "line" in findings and "column" in findings


@mark.passing
def test_builder_parses_values_as_json_with_a_string_fallback():
    """
    `Equals: "true"` and `Equals: true` are different questions, so a typed value keeps its
    JSON type -- while a bare word still means the string, which is what a user expects.
    """
    assert parse_value("true") is True
    assert parse_value("42") == 42
    assert parse_value("null") is None
    assert parse_value('["a", "b"]') == ["a", "b"]
    assert parse_value("production") == "production"
    assert parse_value('"production"') == "production"


# ------------------------------------------------------------------ bindings


@mark.passing
@drives_the_app
async def test_the_app_itself_never_scrolls():
    """
    Each pane scrolls its own content; the application does not. Fixed-height rows summing past
    a short viewport made the Screen scroll, which put a scrollbar down the far right edge of
    the whole app and let the title scroll out of sight, leaving a bare tab row.

    Checked at a short terminal, which is where it appeared.
    """
    app = build_app()
    async with app.run_test(size=(200, 30)) as pilot:
        await pilot.pause()

        assert not app.screen.show_vertical_scrollbar
        scrolling = {w.id for w in app.screen.walk_children() if getattr(w, "show_vertical_scrollbar", False)}
        # Only the editors, which have documents longer than themselves.
        assert scrolling <= {"policy-editor", "input-editor"}, scrolling


@mark.passing
@drives_the_app
async def test_the_wordmark_does_not_cover_the_tabs():
    """
    It shares the tab row on the overlay layer, so it costs no height -- but an overlay
    swallows the whole row it spans, and at full width it hid the tab labels underneath.
    """
    app = build_app()
    async with app.run_test(size=(200, 38)) as pilot:
        await pilot.pause()

        banner = app.query_one("#app-banner")
        # Sits in the right-hand end of the row, clear of the labels at the left.
        assert banner.region.x > 100, banner.region


@mark.passing
@drives_the_app
async def test_number_keys_switch_tabs():
    app = build_app()
    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.press("2")
        await pilot.pause()
        assert app.query_one("#tabs").active == "builder"

        await pilot.press("1")
        await pilot.pause()
        assert app.query_one("#tabs").active == "explorer"
