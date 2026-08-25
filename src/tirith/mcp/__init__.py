"""
Model Context Protocol server for Tirith: let a coding agent author, evaluate and explain
policies without leaving the editor.

Optional, on the same terms as the `tui` extra. Everything that needs the MCP SDK lives in
.server, imported lazily by run() rather than here, so that:

  * `import tirith.mcp` works without the extra installed -- which is what lets the tool-shape
    tests run on CI's Python 3.8 leg, where the SDK cannot be installed at all (it requires
    >=3.10, tirith supports >=3.8); and
  * a user who installed plain `py-tirith` gets an actionable message instead of an ImportError
    traceback.

Why an MCP server at all: an agent asked to "add a policy requiring an Owner tag" will otherwise
guess at the schema, invent condition types that do not exist, and hand back JSON that fails at
evaluation time -- which the human then debugs. These tools replace guessing with the real
schema, the real provider operations, and a real verdict from the real engine.
"""

MCP_EXTRA_HINT = (
    "The Tirith MCP server needs the optional 'mcp' extra:\n"
    "    pip install 'py-tirith[mcp] @ git+https://github.com/StackGuardian/tirith.git'\n"
    "It is optional so that using tirith as a CI gate stays dependency-light. It needs "
    "Python 3.10 or newer; tirith itself supports 3.8."
)


def run(argv=None):
    """
    Entry point for `tirith mcp`. Imports the server lazily; see the module docstring.

    :param argv: Arguments after the `mcp` subcommand.
    :return:     An ExitStatus.
    """
    from .cli import main

    return main(argv or [])
