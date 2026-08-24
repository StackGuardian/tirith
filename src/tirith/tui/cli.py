"""
`tirith ui` -- argument parsing and launch, including the browser-served mode.

Kept separate from app.py so that argument errors and the missing-extra message are reported
without importing the UI toolkit at all, which matters because the commonest reason to reach
this file is not having the extra installed.
"""

import argparse
import json
import os
import shlex
import sys

from .. import __version__
from ..status import ExitStatus
from . import TUI_EXTRA_HINT

DEFAULT_PORT = 8000

# The startup wordmark for `--serve`, drawn in the same three-row style the serving library
# uses for its own, so the terminal announces Tirith rather than the machinery behind it.
# Interpolates the version, which is the thing a reader actually wants from a banner.
# Every row is 21 characters wide. The first draft had the second T one column short, which
# ran its stem into the H beside it -- rows of 21/22/22 rather than 21/21/21.
SERVE_LOGO = (
    "[bold cyan]___ _ ____ _ ___ _  _\n"
    " |  | |__/ |  |  |__|\n"
    " |  | |  \\ |  |  |  |[not bold]  v" + __version__ + "\n"
)


def _load(path, label):
    """
    Read a JSON document from a path, or from stdin when the path is '-'.

    stdin exists so the interface composes with a pipe:

        tirith --json -policy-path p.json -input-path plan.json | tirith ui --result -

    Reading it has a consequence worth handling rather than discovering: once stdin has been
    consumed it is the pipe, not the terminal, and an interactive interface that tries to read
    keys from a spent pipe starts and immediately exits. `_reattach_stdin` puts the terminal
    back. Only one document can come from stdin, since there is only one to give.
    """
    if path != "-":
        from .app import load_json_file

        return load_json_file(path)

    text = sys.stdin.read()
    if not text.strip():
        raise ValueError(f"{label} - was given but stdin was empty")
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"{label} - is not valid JSON: {e.msg} (line {e.lineno}, column {e.colno})")


def _is_missing_toolkit(error):
    """
    Whether an ImportError is the optional extra being absent, rather than a real fault.

    `ImportError.name` is the module that could not be found, so this distinguishes "textual is
    not installed" from "views/playground.py imports a symbol that no longer exists" -- which
    arrives as the same exception type from the same import statement.
    """
    module = getattr(error, "name", None) or ""
    return module.split(".")[0] in ("textual", "textual_serve")


def _reattach_stdin():
    """
    Point stdin back at the terminal after a document was piped in.

    Without this, `... | tirith ui --result -` draws one frame and quits: the interface reads
    keys from stdin, which is an exhausted pipe reporting EOF. Reopening the controlling
    terminal gives it a real input to read.

    Returns whether it worked. It cannot when there is no terminal at all -- a CI job with
    output redirected -- and that is not an error worth failing on here; the caller reports it.
    """
    try:
        tty = open("/dev/tty")
    except OSError:
        return False
    os.dup2(tty.fileno(), 0)
    sys.stdin = tty
    return True


def build_parser():
    parser = argparse.ArgumentParser(
        prog="tirith ui",
        description="Explore policy results, build policies, and experiment in a playground.",
        epilog=(
            "With no arguments, opens the playground with worked examples.\n"
            "Point it at a result document to explore an evaluation you already ran:\n"
            "    tirith -policy-path p.json -input-path i.json --json > result.json\n"
            "    tirith ui --result result.json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    source = parser.add_argument_group("what to open")
    source.add_argument(
        "--result",
        metavar="PATH",
        help="A result document from `tirith --json`, opened in the Explorer. '-' reads stdin.",
    )
    source.add_argument(
        "--policy",
        metavar="PATH",
        help="A policy to open in the Playground.",
    )
    source.add_argument(
        "--input",
        metavar="PATH",
        dest="input_path",
        help="The document to evaluate the policy against.",
    )

    serving = parser.add_argument_group("serving")
    serving.add_argument(
        "--serve",
        action="store_true",
        help="Serve the interface over HTTP instead of running in this terminal.",
    )
    serving.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port for --serve. Default: {DEFAULT_PORT}",
    )
    serving.add_argument(
        "--host",
        default="localhost",
        help="Interface for --serve to bind. Default: localhost",
    )

    return parser


def main(argv):
    parser = build_parser()
    # argv arrives including the `ui` subcommand that dispatched us.
    opts = parser.parse_args(argv[1:] if argv and argv[0] == "ui" else argv)

    for label, path in (("--result", opts.result), ("--policy", opts.policy), ("--input", opts.input_path)):
        if path and path != "-" and not os.path.exists(path):
            print(f"ERROR: {label} {path} does not exist", file=sys.stderr)
            return ExitStatus.ERROR

    if opts.result and opts.policy:
        print(
            "ERROR: --result and --policy are alternatives; --result opens an evaluation that "
            "already ran, --policy opens one to run now.",
            file=sys.stderr,
        )
        return ExitStatus.ERROR

    piped = "-" in (opts.result, opts.policy, opts.input_path)

    if piped and opts.serve:
        # Checked before stdin is read, not after: the served interface is a separate process
        # with its own stdin, so consuming the pipe here would throw the document away and
        # then refuse anyway.
        print("ERROR: --serve cannot read a document from stdin; pass a file path.", file=sys.stderr)
        return ExitStatus.ERROR

    try:
        from .app import build_app
    except ImportError as e:
        # Only the missing toolkit gets the install instruction. This import pulls in the whole
        # package -- four views, the schema, the validator, the engine -- and a blanket except
        # told someone whose textual is installed to install it again, discarding the traceback
        # for the real fault (a typo'd symbol, an API removed in a later release).
        if _is_missing_toolkit(e):
            print(TUI_EXTRA_HINT, file=sys.stderr)
            return ExitStatus.ERROR
        raise

    from . import results

    try:
        report = results.parse_report(_load(opts.result, "--result")) if opts.result else None
        policy = _load(opts.policy, "--policy") if opts.policy else None
        input_document = _load(opts.input_path, "--input") if opts.input_path else None
    except (OSError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return ExitStatus.ERROR

    if opts.serve:
        return _serve(opts, report is not None)

    if piped and not _reattach_stdin():
        print(
            "ERROR: a document was piped in, but there is no terminal to run the interface on.\n"
            "Write it to a file first, or use --serve to open it in a browser.",
            file=sys.stderr,
        )
        return ExitStatus.ERROR

    app = build_app(report=report, policy=policy, input_document=input_document)
    app.run()
    return ExitStatus.SUCCESS


def _serve(opts, has_result):
    """
    Serve the interface over HTTP.

    The server runs the interface as a subprocess and relays it over a websocket, so it takes
    a *command* rather than an app object -- which is why this re-invokes the CLI rather than
    passing the app it would otherwise have built.
    """
    try:
        from textual_serve.server import Server
    except ImportError as e:
        # Narrowed for the same reason as the .app import above.
        if not _is_missing_toolkit(e):
            raise
        print(
            "Serving needs the optional 'tui' extra:\n    pip install 'tirith-iac-governance[tui]'",
            file=sys.stderr,
        )
        return ExitStatus.ERROR

    class TirithServer(Server):
        """A server that announces Tirith rather than the library serving it."""

        async def on_startup(self, app):
            """
            Replace the serving library's startup banner with our own.

            The default prints a large TEXTUAL-SERVE wordmark and the full `python -m` command
            line, which tells the reader about our implementation rather than about the thing
            they just started. Overriding this method is the supported way to change it -- the
            base class documents it as such -- so there is nothing to monkey-patch.
            """
            del app
            self.console.print(SERVE_LOGO, highlight=False)
            self.console.print(f"Policy playground on [link]{self.public_url}[/link]")
            self.console.print("\n[cyan]Press Ctrl+C to quit")

    server = TirithServer(_rebuild_command(opts, has_result), host=opts.host, port=opts.port)
    try:
        server.serve()
    except KeyboardInterrupt:
        return ExitStatus.ERROR_CTRL_C
    return ExitStatus.SUCCESS


def _rebuild_command(opts, has_result):
    """
    The command textual-serve should run for each browser session.

    Absolute paths, because the served subprocess does not necessarily inherit this working
    directory, and a relative --policy that resolved here would not resolve there.
    """
    parts = [sys.executable, "-m", "tirith", "ui"]
    if has_result and opts.result:
        parts += ["--result", os.path.abspath(opts.result)]
    if opts.policy:
        parts += ["--policy", os.path.abspath(opts.policy)]
    if opts.input_path:
        parts += ["--input", os.path.abspath(opts.input_path)]
    return " ".join(_quote(part) for part in parts)


def _quote(part):
    """
    Quote one argument for a shell.

    textual-serve launches with `asyncio.create_subprocess_shell`, so this string really is
    interpreted by sh. Wrapping in double quotes was not enough -- they leave `$`, backticks
    and backslashes live, so a path like `/tmp/my $work/policy.json` had `$work` expanded to
    nothing and every browser session started with a path that did not exist.
    """
    return shlex.quote(part)
