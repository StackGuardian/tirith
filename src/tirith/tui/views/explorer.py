r"""
The Explorer: navigate an evaluation's checks, results, and the resources behind them.

The view this whole package was written for. `pretty_print_result_dict` prints a flat list of
messages, which on a wildcard policy over a real plan is hundreds of lines reading
`"product-456"` is not empty, with nothing to say which resource each came from -- while
the result document has carried the resource's full address, planned action and before/after
values all along.

So: a tree of checks on the left, and the resource detail on the right.
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Static, Tree

from .. import render, results


class ExplorerView(Vertical):
    """Checks on the left, the selected result's detail on the right."""

    def __init__(self, report=None, **kwargs):
        super().__init__(**kwargs)
        self._report = report if report is not None else results.parse_report({})
        # Maps a tree node's id to what it stands for, because Tree nodes carry arbitrary data
        # but comparing node identity across rebuilds is unreliable.
        self._node_targets = {}

    DESCRIPTION = "Read an evaluation down to the resource behind each result. Select a row for detail."

    def compose(self) -> ComposeResult:
        yield Static(self.DESCRIPTION, classes="tab-description")
        yield Static(id="report-summary")
        yield Static(id="report-errors")
        with Horizontal(id="explorer-body"):
            yield Tree("Checks", id="check-tree")
            with VerticalScroll(id="detail-pane"):
                yield Static(id="detail-content")

    def on_mount(self) -> None:
        self._render_report()

    def refresh_report(self, report) -> None:
        """
        Show a new report.

        Callable before this view has mounted its children. The Playground evaluates as it
        mounts and hands its result straight over, and the two views mount in an order Textual
        does not guarantee -- so roughly one run in six the report arrived while
        #report-summary did not yet exist, raising NoMatches out of a tab the user had not
        even opened.

        Stores it and defers the draw rather than skipping it: skipping would lose whichever
        report lost the race, and that is the report the user asked to see.
        """
        self._report = report
        if self.is_mounted:
            self._render_report()

    def _render_report(self) -> None:
        """Draw the stored report. Only reached once this view's own children exist."""
        report = self._report
        self._node_targets = {}

        summary = self.query_one("#report-summary", Static)
        summary.update(render.report_headline(report))

        errors = self.query_one("#report-errors", Static)
        if report.errors:
            errors.update("\n".join(f"! {render.escape(e)}" for e in report.errors))
            errors.display = True
        else:
            errors.display = False

        tree = self.query_one("#check-tree", Tree)
        tree.clear()
        tree.root.expand()

        if not report.checks:
            tree.root.label = "No checks"
            self._show_empty()
            return

        tree.root.label = f"{len(report.checks)} checks"

        first_failing_node = None
        for check in report.checks:
            node = tree.root.add(render.check_label(check), expand=check.passed is False)
            self._node_targets[node.id] = ("check", check, None)

            for result in check.results:
                leaf = node.add_leaf(render.result_label(result))
                self._node_targets[leaf.id] = ("result", check, result)
                # Open on the first failure. A passing policy is read top-down, but a failing
                # one is opened to find out what failed, and making that the default saves
                # the user hunting for it.
                if first_failing_node is None and result.passed is False:
                    first_failing_node = leaf

        target = first_failing_node
        if target is not None:
            tree.select_node(target)
            tree.scroll_to_node(target)
            self._show_result(*self._node_targets[target.id][1:])
        else:
            self._show_check(report.checks[0])

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        entry = self._node_targets.get(event.node.id)
        if entry is None:
            return
        kind, check, result = entry
        if kind == "check":
            self._show_check(check)
        else:
            self._show_result(check, result)

    # Highlight follows the cursor as it moves with the arrow keys, so the detail pane tracks
    # keyboard navigation rather than only responding to Enter.
    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        self.on_tree_node_selected(Tree.NodeSelected(event.node))

    def _detail(self) -> Static:
        return self.query_one("#detail-content", Static)

    def _show_empty(self) -> None:
        self._detail().update("[dim]Nothing to show. Evaluate a policy to see its results here.[/dim]")

    def _show_check(self, check) -> None:
        lines = [
            f"{render.status_markup(check.status, check.id)}",
            "",
        ]
        if check.description:
            lines.append(render.escape(check.description))
            lines.append("")
        lines.append(f"[dim]{render.escape(check.summary)}[/dim]")

        failing = check.failing_results()
        if failing:
            lines.append("")
            lines.append("[bold]Failing resources[/bold]")
            for result in failing:
                name = result.resource.label or render.escape(result.message)
                lines.append(f"  ✘ {render.escape(name)}")

        self._detail().update("\n".join(lines))

    def _show_result(self, check, result) -> None:
        lines = [
            render.status_markup(result.status, check.id),
            "",
            render.escape(result.message),
        ]

        resource_lines = render.resource_lines(result)
        if resource_lines:
            lines.append("")
            lines.append("[bold]Resource[/bold]")
            lines.extend(f"  {line}" for line in resource_lines)

        diff_lines = render.attribute_diff_lines(result)
        if diff_lines:
            lines.append("")
            lines.append("[bold]Changed attributes[/bold]")
            lines.extend(f"  {line}" for line in diff_lines)
        elif result.raw_meta and not resource_lines:
            # A provider recorded something we do not model. Better to show it raw than to
            # silently drop detail the user came here for.
            lines.append("")
            lines.append("[bold]Metadata[/bold]")
            lines.append(f"  {render.escape(render.format_value(result.raw_meta, 800))}")

        self._detail().update("\n".join(lines))
