"""
A modal file browser, for choosing a policy or an input document.

Typing a path was the first version and it asks the user to already know where the file is,
which is the thing a browser is for. This walks the filesystem instead: arrow keys to move,
Enter to open a directory or choose a file.

Filtered to the documents this program can actually read -- JSON and YAML -- plus directories
to descend into. Hidden entries are skipped, because `.git` and `.venv` are noise here and
expanding them is slow.
"""

import os

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DirectoryTree, Input, Static

# What the engine can parse. YAML is included because the core reads .yaml/.yml inputs, even
# though the playground's editors show JSON.
READABLE_SUFFIXES = {".json", ".yaml", ".yml", ".jsonc"}

# Directories that are never worth walking into from a project root, and are often enormous.
SKIP_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".terraform",
    "dist",
    "build",
}


class DocumentTree(DirectoryTree):
    """A DirectoryTree showing only directories and documents the engine can read."""

    def filter_paths(self, paths):
        keep = []
        for path in paths:
            if path.name.startswith("."):
                continue
            if path.is_dir():
                if path.name not in SKIP_DIRECTORIES:
                    keep.append(path)
                continue
            if path.suffix.lower() in READABLE_SUFFIXES:
                keep.append(path)
        # Directories first, then files, each alphabetically -- the order a file manager uses,
        # rather than the arbitrary one the filesystem returns.
        return sorted(keep, key=lambda p: (not p.is_dir(), p.name.lower()))


class FilePicker(ModalScreen[str]):
    """
    Choose a file. Dismissed with the chosen path, or with None if cancelled.

    A ModalScreen returning a value, so the caller awaits a path rather than wiring up
    callbacks: `path = await self.app.push_screen_wait(FilePicker("policy"))`.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        # Left and right walk the filesystem, the way a file manager does. A DirectoryTree can
        # only ever descend from its root, so without re-rooting the picker could reach nothing
        # outside the directory it opened in -- and the plan you want to check is usually in
        # another repo entirely.
        #
        # Tree leaves plain left/right unbound (it uses shift+left / shift+right for parent and
        # sibling), so these take nothing away.
        Binding("left,backspace", "go_up", "Parent"),
        Binding("right", "go_into", "Open"),
        Binding("~", "go_home", "Home"),
    ]

    def __init__(self, slot: str, start_directory: str = "."):
        """
        :param slot:            "policy" or "input", named in the title so it is clear which
                                editor the chosen file will fill.
        :param start_directory: Where to open. Defaults to the working directory, which is
                                where a user running this in their repo expects to start.
        """
        super().__init__()
        self._slot = slot
        self._directory = os.path.abspath(start_directory)

    def compose(self) -> ComposeResult:
        with Vertical(id="file-picker"):
            yield Static(f"Open a file as the {self._slot}", id="file-picker-title")
            yield Static(self._directory, id="file-picker-location")
            yield Static(
                "↑↓ move · → into · ← back · Enter choose · ~ home · Esc cancel · .json .yaml .yml",
                id="file-picker-help",
            )
            yield DocumentTree(self._directory, id="file-picker-tree")
            # Kept as an escape hatch: a path that is quicker to paste than to navigate to,
            # and the only way to reach one whose directory is faster to type than to walk.
            yield Input(placeholder="…or type a path and press Enter", id="file-picker-path")
            with Horizontal(id="file-picker-buttons"):
                yield Button("← Back", id="file-picker-up")
                yield Button("Cancel", id="file-picker-cancel")

    def on_mount(self) -> None:
        self.query_one("#file-picker-tree", DirectoryTree).focus()

    def _show_directory(self, directory: str) -> None:
        """
        Re-root the tree at a new directory.

        Reassigning `path` rather than rebuilding the widget, which keeps focus where it is
        and is what DirectoryTree supports for changing root.
        """
        self._directory = os.path.abspath(directory)
        tree = self.query_one("#file-picker-tree", DocumentTree)
        tree.path = self._directory
        tree.reload()
        self.query_one("#file-picker-location", Static).update(self._directory)
        tree.focus()

    def action_go_up(self) -> None:
        parent = os.path.dirname(self._directory)
        # dirname("/") is "/", so this stops at the filesystem root rather than looping.
        if parent and parent != self._directory:
            self._show_directory(parent)

    def action_go_into(self) -> None:
        """
        Re-root at the directory under the cursor, so right/left are inverses of each other.

        Descending by re-rooting rather than expanding in place: it keeps the tree showing one
        directory at a time, which is what makes `left` a reliable way back. Expanding instead
        would leave the root where it was and the two keys would stop being symmetrical.
        """
        node = self.query_one("#file-picker-tree", DocumentTree).cursor_node
        entry = getattr(node, "data", None)
        path = getattr(entry, "path", None)
        if path and os.path.isdir(path):
            self._show_directory(str(path))

    def action_go_home(self) -> None:
        self._show_directory(os.path.expanduser("~"))

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.dismiss(str(event.path))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        raw = event.value.strip().strip("'\"")
        if not raw:
            return
        path = os.path.expanduser(raw)
        # A directory means "take me there", not "open this as a document" -- typing a path is
        # often the fastest way to get to a folder deep in someone else's checkout.
        if os.path.isdir(path):
            event.input.value = ""
            self._show_directory(path)
            return
        self.dismiss(path)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "file-picker-cancel":
            self.action_cancel()
        elif event.button.id == "file-picker-up":
            self.action_go_up()

    def action_cancel(self) -> None:
        # Dismissing with None rather than "" so the caller can tell "cancelled" from a path,
        # and never has to guess at an empty string.
        self.dismiss(None)
