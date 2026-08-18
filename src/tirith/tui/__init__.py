"""
Interactive interface for Tirith: explore results, build policies, experiment in a playground.

Optional. Everything that needs the UI toolkit lives in .app and its views, imported lazily by
run() rather than here, so that:

  * `import tirith.tui.schema` works without the extra installed -- which is what lets the
    schema drift-guard tests run on CI's Python 3.8 leg, where the toolkit cannot be installed
    at all (it requires >=3.9, tirith supports >=3.8); and
  * a user who installed plain `py-tirith` gets an actionable message instead of an
    ImportError traceback.
"""

TUI_EXTRA_HINT = (
    "The Tirith interactive interface needs the optional 'tui' extra:\n"
    "    pip install 'py-tirith[tui]'\n"
    "It is optional so that using tirith as a CI gate stays dependency-light. It needs "
    "Python 3.9 or newer; tirith itself supports 3.8."
)


def run(argv=None):
    """
    Entry point for `tirith ui`. Imports the app lazily; see the module docstring.

    :param argv: Arguments after the `ui` subcommand.
    :return:     An ExitStatus.
    """
    from .cli import main

    return main(argv or [])
