"""
`tirith mcp` -- argument parsing and launch.

Kept separate from server.py so that argument errors and the missing-extra message are reported
without importing the MCP SDK at all, which matters because the commonest reason to reach this
file is not having the extra installed.
"""

import argparse
import sys

from .. import __version__
from ..status import ExitStatus
from . import MCP_EXTRA_HINT


def _is_missing_sdk(error):
    """
    Whether an ImportError is the optional extra being absent, rather than a real fault.

    `ImportError.name` is the module that could not be found, so this distinguishes "mcp is not
    installed" from "server.py imports a symbol that no longer exists" -- which arrives as the
    same exception type from the same import statement.
    """
    module = getattr(error, "name", None) or ""
    return module.split(".")[0] == "mcp"


def main(argv=None) -> ExitStatus:
    parser = argparse.ArgumentParser(
        prog="tirith mcp",
        description=(
            "Run Tirith as a Model Context Protocol server, so a coding agent can evaluate "
            "policies, lint them, look up the schema and explain a result."
        ),
        epilog=(
            "Speaks MCP over stdio; it is started by your editor or agent, not run by hand. "
            "It makes no network calls and writes nothing to disk."
        ),
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.parse_args(list(argv or [])[1:])

    try:
        from .server import serve
    except ImportError as error:
        if _is_missing_sdk(error):
            print(MCP_EXTRA_HINT, file=sys.stderr)
            return ExitStatus.ERROR
        raise

    try:
        serve()
    except KeyboardInterrupt:
        return ExitStatus.ERROR_CTRL_C
    return ExitStatus.SUCCESS
