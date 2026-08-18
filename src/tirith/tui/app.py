"""
The app shell: three tabs over one shared evaluation.

The three views are tabs rather than separate screens so they can share state. Building a
policy in the Builder and opening it in the Playground, then reading the failure in the
Explorer, is one continuous task -- making each a separate program would mean saving a file
between every step.

Requires textual. Nothing else in this package does; see tui/__init__.py.
"""

import json
import os

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Static, TabbedContent, TabPane

from . import results
from .views.builder import BuilderView
from .views.explorer import ExplorerView
from .views.playground import PlaygroundView

CSS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.css")

# The wordmark. A terminal has one font size, so a title is made prominent by weight, spacing
# and a full-width coloured bar rather than by points.
#
# Drawn block glyphs were the obvious way to make it literally taller and were tried first:
# at this size the half-block `█ █` that has to stand for an H is indistinguishable from two
# `I`s, so TIRITH read as TIRITII. Letter-spaced bold caps stay unambiguous, which matters
# more for a name than height does.
BANNER = "[b]T I R I T H[/b]   [dim]Policy as Code[/dim]"


class TirithApp(App):
    """Explore results, build policies, experiment."""

    CSS_PATH = CSS_PATH
    TITLE = "TIRITH"
    SUB_TITLE = "Policy as Code"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("1", "show_tab('explorer')", "Explorer"),
        Binding("2", "show_tab('builder')", "Builder"),
        Binding("3", "show_tab('playground')", "Playground"),
        Binding("r", "rerun", "Re-run"),
    ]

    def __init__(self, report=None, start_tab="playground", policy=None, input_document=None, **kwargs):
        super().__init__(**kwargs)
        self._initial_report = report if report is not None else results.parse_report({})
        # Open on the Explorer when given something to explore, and on the Playground
        # otherwise -- an empty Explorer has nothing to say.
        self._start_tab = start_tab
        self._initial_policy = policy
        self._initial_input = input_document
        # See _adopt_report: protects an explicitly-opened --result from being overwritten by
        # the example the Playground loads while mounting.
        self._explorer_is_pinned = report is not None

    def compose(self) -> ComposeResult:
        # The wordmark shares the tab row rather than occupying a band of its own. As a
        # separate row it cost height that the Builder's form and the Playground's editors
        # need, and on a short terminal it pushed the layout past the viewport -- which made
        # the whole Screen scroll, putting a scrollbar down the edge of the application and
        # letting the title scroll out of sight.
        # Sits on the overlay layer, drawn over the right-hand end of the tab row, so it costs
        # no height at all. Nesting it in a Horizontal with the tabs would have worked too, but
        # would constrain every pane inside that container for the sake of one label.
        yield Static(BANNER, id="app-banner")
        with TabbedContent(initial=self._start_tab, id="tabs"):
            with TabPane("Explorer", id="explorer"):
                yield ExplorerView(report=self._initial_report, id="explorer-view")
            with TabPane("Builder", id="builder"):
                yield BuilderView(on_policy_built=self._open_policy_in_playground, id="builder-view")
            with TabPane("Playground", id="playground"):
                yield PlaygroundView(
                    on_report=self._adopt_report,
                    on_user_action=self._release_explorer,
                    id="playground-view",
                )
        yield Footer()

    def on_mount(self) -> None:
        """Load anything supplied on the command line, once the widgets exist."""
        playground = self.query_one("#playground-view", PlaygroundView)
        if self._initial_policy is not None:
            playground.load_documents(self._initial_policy, self._initial_input)
        elif self._initial_input is not None:
            playground.load_documents(None, self._initial_input)

        # Someone who named their own policy and input came to see how it did, so show them
        # the results rather than the editor they would have to leave to find them. Switched
        # here rather than through `initial=`, because the Playground has to mount and
        # evaluate before there is anything for the Explorer to show.
        if self._initial_policy is not None and self._initial_input is not None:
            self.query_one("#tabs", TabbedContent).active = "explorer"

    # ---------------------------------------------------------------- wiring

    def _adopt_report(self, report) -> None:
        """
        Keep the Explorer showing whatever the Playground last evaluated.

        Except when the user opened a specific result with `--result`, which stays on screen
        until they run something themselves. The Playground evaluates while mounting -- once
        for the example it loads, and again if the command line supplied an --input -- so
        anything that unpins on the first adopt is defeated by the second: the Explorer ended
        up holding example 01 evaluated against the user's plan.

        Released by _release_explorer, called from the deliberate actions (Run, Re-run, an
        edit, opening a document) rather than counted down here.
        """
        if self._explorer_is_pinned:
            return
        self.query_one("#explorer-view", ExplorerView).refresh_report(report)

    def _release_explorer(self) -> None:
        """The user has run something of their own, so the Explorer follows the Playground again."""
        self._explorer_is_pinned = False

    def _open_policy_in_playground(self, policy) -> None:
        self.query_one("#playground-view", PlaygroundView).load_policy(policy)
        self.query_one("#tabs", TabbedContent).active = "playground"

    # --------------------------------------------------------------- actions

    def action_show_tab(self, tab: str) -> None:
        self.query_one("#tabs", TabbedContent).active = tab

    def action_rerun(self) -> None:
        self.query_one("#playground-view", PlaygroundView).evaluate_now()


def build_app(report=None, policy=None, input_document=None) -> TirithApp:
    """
    Construct the app, optionally pre-loaded.

    :param report:         A parsed result document to open in the Explorer.
    :param policy:         A policy to open in the Playground.
    :param input_document: The document to evaluate it against.
    """
    return TirithApp(
        report=report,
        start_tab="explorer" if report is not None else "playground",
        policy=policy,
        input_document=input_document,
    )


def load_json_file(path: str):
    """Read a JSON file, raising a clear message rather than a bare exception."""
    with open(path, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"{path} is not valid JSON: {e.msg} (line {e.lineno}, column {e.colno})")
