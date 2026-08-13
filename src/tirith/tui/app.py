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
        # A drawn wordmark rather than Header. A terminal has one font size, so "bigger" means
        # taller glyphs -- three rows of block characters -- and Header cannot do that. It also
        # centres properly, which is the other half of the ask.
        yield Static(BANNER, id="app-banner")
        with TabbedContent(initial=self._start_tab, id="tabs"):
            with TabPane("Explorer", id="explorer"):
                yield ExplorerView(report=self._initial_report, id="explorer-view")
            with TabPane("Builder", id="builder"):
                yield BuilderView(on_policy_built=self._open_policy_in_playground, id="builder-view")
            with TabPane("Playground", id="playground"):
                yield PlaygroundView(on_report=self._adopt_report, id="playground-view")
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

        Except when the user opened a specific result with `--result`: the Playground loads an
        example as it mounts, and adopting that would silently replace the evaluation they
        asked to look at with an unrelated one. The first playground run after that is the
        user's own doing, so it takes over from then on.
        """
        if self._explorer_is_pinned:
            self._explorer_is_pinned = False
            return
        self.query_one("#explorer-view", ExplorerView).refresh_report(report)

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
