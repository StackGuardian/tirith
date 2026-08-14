"""
The Playground: edit a policy and an input side by side and watch the verdict move.

Load an example, change something, see what happens. That loop is the fastest way to learn a
policy language, and it is what the repository's fixtures cannot offer -- they teach the
engine's authors, not its users.

Evaluation runs on every edit, debounced. Everything that can go wrong while typing -- JSON
that does not parse yet, a policy missing half its keys, a provider that raises -- is caught
and reported in the findings pane, because during editing the broken state is the normal state
and a traceback would be the usual output rather than the exception.
"""

import json
import os

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Markdown, Select, Static, TextArea

from .. import examples as examples_module
from .. import render, results, schema, validate
from .filepicker import FilePicker
from ...core.core import start_policy_evaluation_from_dict

# How long to wait after the last keystroke before re-evaluating. Long enough not to run on
# every character of a pasted document, short enough to feel immediate.
DEBOUNCE_SECONDS = 0.4


class PlaygroundView(Vertical):
    """A description strip, then examples and editors on the left, results on the right."""

    DESCRIPTION = "Edit a policy or its input and watch the verdict change. Pick an example to start."

    def __init__(self, on_report=None, on_user_action=None, **kwargs):
        super().__init__(**kwargs)
        # Called with each new report so the Explorer tab can show the same evaluation.
        self._on_report = on_report
        # Called when the user does something deliberate here -- edits a document, presses Run,
        # opens a file, picks an example. It tells the app that a report opened with --result
        # is no longer what they are looking at. Mount-time evaluation does not call it.
        self._on_user_action = on_user_action
        self._examples = examples_module.load_examples()
        self._timer = None
        self._current_example = None
        # Which editor a chosen file will fill; set by an Open button.
        self._pending_slot = "input"

    def compose(self) -> ComposeResult:
        # The example picker belongs to the whole tab, not to either editor: choosing one
        # replaces the policy *and* the input together. Sitting it in the editor column made it
        # look like a third document, and its bordered Select needs three rows next to
        # one-row toolbars, which is what made that corner look wrong.
        with Horizontal(id="playground-header"):
            # Labelled and placed immediately after the sentence that tells you to use it.
            # Unlabelled and pushed to the far right, it read as a status field showing the
            # name of something rather than as the control that changes it.
            yield Static("Example:", id="example-label")
            # compact drops the border, so it sits on one row inside the band rather than as a
            # bordered box floating in it.
            yield Select(
                [(e.title, i) for i, e in enumerate(self._examples)],
                prompt="Choose one",
                compact=True,
                id="example-select",
            )
            yield Button("About", id="toggle-about", classes="header-button")
            yield Static(self.DESCRIPTION, id="playground-description")

        with Horizontal(id="playground-body"):
            with Vertical(id="playground-editors"):
                # Each editor carries its own actions, next to the thing they act on.
                with Horizontal(classes="editor-toolbar"):
                    yield Static("Policy", classes="toolbar-label")
                    yield Button("Copy", id="copy-policy", classes="icon-button")
                    yield Button("Open", id="open-policy", classes="icon-button")
                    yield Button("Clear", id="clear-policy", classes="icon-button")
                yield TextArea(id="policy-editor", language="json", soft_wrap=False)

                with Horizontal(classes="editor-toolbar"):
                    yield Static("Input document", classes="toolbar-label", id="input-label")
                    yield Button("Copy", id="copy-input", classes="icon-button")
                    yield Button("Open", id="open-input", classes="icon-button")
                    yield Button("Clear", id="clear-input", classes="icon-button")
                yield TextArea(id="input-editor", language="json", soft_wrap=False)

            with Vertical(id="playground-results"):
                yield Static("", id="playground-status")
                yield Static("", id="playground-notice")
                yield Static("", id="findings-list")
                yield VerticalScroll(Static(id="playground-output"), id="playground-output-scroll")
                yield Horizontal(
                    Button("Run", variant="primary", id="run-now"),
                    Button("Reset example", id="reset-example"),
                    id="playground-buttons",
                )
                # Hidden until asked for. The notes are worth reading once per example and
                # then permanently in the way of the results, which are the reason to be here.
                yield Static("About this example", classes="editor-label", id="about-label")
                yield VerticalScroll(Markdown("", id="example-detail"), id="about-scroll")

    def on_mount(self) -> None:
        # Both start hidden: the notes are read once and then in the way, and the path box is
        # only relevant once an Open button has been pressed.
        self.query_one("#about-scroll").display = False
        self.query_one("#about-label", Static).display = False

        if self._examples:
            self.load_example(self._examples[0])
            # Select without firing Changed, which would re-load the example we just loaded.
            with self.prevent(Select.Changed):
                self.query_one("#example-select", Select).value = 0
        else:
            self._set_status("[dim]No examples are bundled with this install.[/dim]")

    def _notify(self, message: str) -> None:
        """
        Confirm an action that has no visible result of its own -- a copy, a file load.

        Its own row rather than the status line: the status line holds the verdict, and the
        debounced re-evaluation overwrites whatever is there a moment later, so a confirmation
        put in it disappeared before it could be read.
        """
        self.query_one("#playground-notice", Static).update(f"[dim]{render.escape(message)}[/dim]")

    # --------------------------------------------------------------- loading

    def load_example(self, example) -> None:
        self._current_example = example
        # Suppressed for the same reason as in load_documents: these are our writes, not edits.
        with self.prevent(TextArea.Changed):
            self.query_one("#policy-editor", TextArea).text = example.policy_json
            self.query_one("#input-editor", TextArea).text = example.input_json
        self.query_one("#example-detail", Markdown).update(example.about)
        self.evaluate_now()

    def load_policy(self, policy: dict) -> None:
        """Used by the Builder's 'Open in playground' button."""
        self.load_documents(policy, None)

    def load_documents(self, policy=None, input_document=None) -> None:
        """
        Replace either editor, leaving the other alone.

        Both are optional so `--policy` without `--input` keeps whichever example was loaded
        as the document to evaluate against, rather than blanking it and reporting an error.
        """
        # Suppresses the Changed events these writes raise, rather than flagging and ignoring
        # them: the events are delivered a frame later, so any flag set around the assignment
        # has already been cleared by the time the handler runs. Without this the handler
        # wipes the confirmation the caller is about to display.
        with self.prevent(TextArea.Changed):
            if policy is not None:
                self.query_one("#policy-editor", TextArea).text = json.dumps(policy, indent=2)
                # The loaded policy is no longer the example's, so offering to "reset" to an
                # example the user did not load would be misleading.
                self._current_example = None
                self.query_one("#example-detail", Markdown).update("")
            if input_document is not None:
                self.query_one("#input-editor", TextArea).text = json.dumps(input_document, indent=2)
        self.evaluate_now()

    def on_select_changed(self, event: Select.Changed) -> None:
        """
        Load the chosen example, or clear both editors when the prompt row is chosen.

        The blank value is `Select.NULL`, a NoSelection sentinel. Not `Select.BLANK`, which is
        the literal `False` -- comparing against that let the sentinel through to int() and
        crashed the app the first time anyone opened the dropdown and picked the prompt.
        """
        if event.select.id != "example-select":
            return
        self._note_user_action()

        if event.value is Select.NULL:
            # Choosing the prompt means "none of these": empty both editors, so it is a way to
            # start from nothing rather than a no-op that leaves the last example loaded.
            self._current_example = None
            self.query_one("#example-detail", Markdown).update("")
            self.query_one("#policy-editor", TextArea).text = ""
            self.query_one("#input-editor", TextArea).text = ""
            self.evaluate_now()
            return

        index = int(event.value)
        if 0 <= index < len(self._examples):
            self.load_example(self._examples[index])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        actions = {
            "run-now": self.evaluate_now,
            "reset-example": self._reset_example,
            "toggle-about": self._toggle_about,
            "copy-policy": lambda: self._copy("#policy-editor", "Policy"),
            "copy-input": lambda: self._copy("#input-editor", "Input document"),
            "clear-policy": lambda: self._clear("#policy-editor"),
            "clear-input": lambda: self._clear("#input-editor"),
            "open-policy": lambda: self._prompt_for_file("policy"),
            "open-input": lambda: self._prompt_for_file("input"),
        }
        action = actions.get(event.button.id or "")
        if action:
            self._note_user_action()
            action()

    def _note_user_action(self) -> None:
        """Tell the app the user has taken over, so a --result report stops being pinned."""
        if self._on_user_action:
            self._on_user_action()

    # ------------------------------------------------------------- toolbars

    def _reset_example(self) -> None:
        if self._current_example:
            self.load_example(self._current_example)

    def _copy(self, selector: str, label: str) -> None:
        """
        Put an editor's contents on the system clipboard.

        Textual routes this through the terminal's OSC 52 escape, which most terminals honour
        and some do not -- and there is no reply to tell us which. So the message says what was
        attempted rather than claiming success.
        """
        text = self.query_one(selector, TextArea).text
        if not text.strip():
            self._notify(f"{label} is empty; nothing to copy.")
            return
        self.app.copy_to_clipboard(text)
        self._notify(f"{label} sent to the clipboard ({len(text)} characters).")

    def _clear(self, selector: str) -> None:
        self.query_one(selector, TextArea).text = ""
        self.evaluate_now()

    def _prompt_for_file(self, slot: str) -> None:
        """
        Open the file browser and load whatever comes back.

        A browser rather than the path box this replaced: typing a path assumes you already
        know where the file is, which is the thing you open a file dialog to find out.
        """
        self._pending_slot = slot

        def loaded(path):
            # None means cancelled, which is not an error and needs no message.
            if path:
                self._load_path(path, slot)

        self.app.push_screen(FilePicker(slot), loaded)

    def _toggle_about(self) -> None:
        showing = not self.query_one("#about-scroll").display
        self.query_one("#about-scroll").display = showing
        self.query_one("#about-label", Static).display = showing

    def _load_path(self, raw_path, slot=None):
        """
        Read a file into the policy editor, the input editor, or whichever fits.

        :param raw_path: Path to read. `~` and surrounding quotes are tolerated, since both
                         arrive from ordinary shell copy-paste.
        :param slot:     "policy", "input", or None to decide from the document itself. A
                         policy is recognisable -- an object with `evaluators` and `meta` --
                         so the guess is reliable when the caller has no preference.
        """
        path = os.path.expanduser(str(raw_path).strip().strip("'\""))
        try:
            with open(path, encoding="utf-8") as f:
                document = json.load(f)
        except FileNotFoundError:
            self._report_problem(f"No such file: {path}")
            return
        except IsADirectoryError:
            self._report_problem(f"{path} is a directory, not a JSON file.")
            return
        except OSError as e:
            self._report_problem(f"Could not read {path}: {e}")
            return
        except json.JSONDecodeError as e:
            self._report_problem(f"{path} is not valid JSON: {e.msg} (line {e.lineno}, column {e.colno})")
            return

        if slot is None:
            slot = "policy" if _looks_like_a_policy(document) else "input"

        if slot == "policy":
            self.load_documents(policy=document)
        else:
            self.load_documents(input_document=document)

        self._notify(f"Loaded {os.path.basename(path)} as the {slot}.")

    # ------------------------------------------------------------ evaluation

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        del event
        # Typing here is a user action; programmatic writes suppress this event entirely.
        self._note_user_action()
        # Typing makes a previous confirmation ("Loaded plan.json") stale. Programmatic writes
        # do not reach here at all -- load_documents suppresses their Changed events -- so this
        # only ever runs for a real edit.
        self.query_one("#playground-notice", Static).update("")
        # Debounced rather than immediate: a paste would otherwise run the engine once per
        # character, and each run walks the whole input document.
        if self._timer is not None:
            self._timer.stop()
        self._timer = self.set_timer(DEBOUNCE_SECONDS, self.evaluate_now)

    def evaluate_now(self) -> None:
        policy_text = self.query_one("#policy-editor", TextArea).text
        input_text = self.query_one("#input-editor", TextArea).text

        policy, policy_error = _parse_json(policy_text, "Policy")
        if policy_error:
            self._report_problem(policy_error)
            return

        input_document, input_error = _parse_json(input_text, "Input document")
        if input_error:
            self._report_problem(input_error)
            return

        findings = validate.check_policy(policy)
        errors = [f for f in findings if f.severity == "error"]
        if not isinstance(policy, dict):
            # Valid JSON but not an object -- a bare list or string parses fine and would
            # otherwise reach the engine and raise. check_policy reports it; stop here so the
            # engine is never handed something it cannot read.
            self._show_findings(findings)
            self._set_status("[red]✘ Cannot evaluate[/red]")
            self.query_one("#playground-output", Static).update("")
            return
        if errors:
            # Still shown as findings rather than refusing to run: a half-written policy is
            # the normal state here, and the findings say what is missing.
            self._show_findings(findings)
            self._set_status("[yellow]▲ Policy is incomplete[/yellow]")
            self.query_one("#playground-output", Static).update("")
            return

        provider = policy.get("meta", {}).get("required_provider", "")
        self._label_expected_input(provider)
        findings = findings + validate.check_input_document(input_document, provider)

        try:
            raw_result = start_policy_evaluation_from_dict(policy, input_document)
        except Exception as e:
            # The engine raises for things the validator cannot see -- an unsupported operator
            # in eval_expression reaches here as ValueError. Report it as a finding; a
            # traceback in a playground is a bug in the playground.
            self._report_problem(f"{type(e).__name__}: {e}")
            return

        report = results.parse_report(raw_result)
        self._show_findings(findings)
        self._set_status(render.report_headline(report))
        self._show_results(report)

        if self._on_report:
            self._on_report(report)

    def _label_expected_input(self, provider_name: str) -> None:
        """
        Say what document the policy's provider expects, above the editor it goes in.

        The commonest way to waste ten minutes here is feeding the right JSON to the wrong
        provider: a terraform plan under `stackguardian/kubernetes` reports that no kind
        matched, which is true and says nothing about the actual mistake.
        """
        described = schema.PROVIDERS.get(provider_name)
        label = self.query_one("#input-label", Static)
        if described is None:
            label.update("Input document")
            return
        label.update(f"Input document  [dim]— {render.escape(described.input_hint)}[/dim]")

    def _report_problem(self, message: str) -> None:
        self._set_status("[red]✘ Cannot evaluate[/red]")
        self.query_one("#findings-list", Static).update(f"[red]{render.escape(message)}[/red]")
        self.query_one("#playground-output", Static).update("")

    def _set_status(self, markup: str) -> None:
        self.query_one("#playground-status", Static).update(markup)

    def _show_findings(self, findings) -> None:
        widget = self.query_one("#findings-list", Static)
        if not findings:
            widget.update("")
            return
        widget.update("\n".join(render.finding_markup(f) for f in findings[:6]))

    def _show_results(self, report) -> None:
        lines = []
        for check in report.checks:
            lines.append(render.check_label(check))
            for result in check.results:
                lines.append(f"    {render.result_label(result)}")
                if result.resource.label:
                    lines.append(f"      [dim]{render.escape(result.message)}[/dim]")
            lines.append("")

        if report.errors:
            lines.append("[red]Errors[/red]")
            lines.extend(f"  {render.escape(e)}" for e in report.errors)

        if report.eval_expression:
            lines.append(f"[dim]Expression: {render.escape(report.eval_expression)}[/dim]")

        self.query_one("#playground-output", Static).update("\n".join(lines))


def _looks_like_a_policy(document) -> bool:
    """
    Whether a loaded document is a Tirith policy rather than something to evaluate.

    Structural, not name-based: a policy is an object carrying `evaluators`, which is a key no
    plan, manifest or cost report has. Guessing from the filename would be wrong as often as
    right -- plenty of policies are called policy.json, but plenty are not.
    """
    return isinstance(document, dict) and "evaluators" in document and "meta" in document


def _parse_json(text: str, label: str):
    """
    Parse an editor buffer, returning (value, error_message).

    The error carries the line and column, because in a 200-line plan "Expecting ',' delimiter"
    on its own is not enough to find the typo.
    """
    if not text.strip():
        return None, f"{label} is empty."
    try:
        return json.loads(text), None
    except json.JSONDecodeError as e:
        return None, f"{label} is not valid JSON: {e.msg} (line {e.lineno}, column {e.colno})"
