"""
The MCP protocol layer.

Thin on purpose: every tool's behaviour lives in tools.py, which imports nothing from the SDK.
This file only describes those functions to a client and adapts their return values. Keeping the
split means the logic is testable on Python 3.8, where the SDK cannot be installed.

Transport is stdio. The server reads a policy and a document it is given and returns a verdict;
it opens no sockets, makes no network calls and writes nothing to disk, so pointing an agent at
it cannot change anyone's infrastructure.
"""

import json

from . import tools

# The SDK renamed its server class between generations: 1.x exposes
# `mcp.server.fastmcp.FastMCP`, 2.x exposes `mcp.server.mcpserver.MCPServer`. Both keep the same
# `.tool()` decorator and the same `.run(transport=...)`, so supporting each is an import shim
# rather than two code paths -- and worth doing, because which one a user has installed is not
# something this project gets to choose.
try:  # SDK 2.x
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # pragma: no cover - depends on which SDK generation is installed
    from mcp.server.fastmcp import FastMCP as _Server  # SDK 1.x

mcp = _Server("tirith")


def _json(payload):
    return json.dumps(payload, indent=2, default=str)


@mcp.tool()
def evaluate(policy: dict, document: dict, variables: dict = None) -> str:
    """
    Run a Tirith policy against an input document and return the real verdict.

    Use this instead of reasoning about whether a policy is correct. A policy that matches
    nothing looks identical to one that works until it is evaluated, and the result distinguishes
    passed, failed and unevaluated -- where unevaluated is NOT a pass.

    :param policy:    The policy, as a JSON object.
    :param document:  The document to evaluate: a terraform plan, state, Infracost breakdown,
                      Kubernetes manifest or arbitrary JSON, matching the policy's provider.
    :param variables: Optional values for {{ var.x }} placeholders in the policy.
    """
    return _json(tools.evaluate(policy, document, variables))


@mcp.tool()
def lint_policy(policy: dict) -> str:
    """
    Check a policy's shape before running it, and report what would go wrong.

    Catches an unknown condition type, a missing eval_expression, and evaluators the expression
    never references. Worth calling on every policy you write or edit: the engine reports several
    of these mistakes as an ordinary failed check, which reads as a real infrastructure violation.

    :param policy: The policy, as a JSON object.
    """
    return _json(tools.lint_policy(policy))


@mcp.tool()
def describe_provider(provider: str = None) -> str:
    """
    List the providers a policy can read, the operation_type values each accepts, and every
    available condition type.

    Call this before writing a policy rather than guessing at the vocabulary. Omit the argument
    for all providers, or name one for its documentation link.

    :param provider: Optional provider name, e.g. 'terraform_plan'.
    """
    return _json(tools.describe_provider(provider))


@mcp.tool()
def explain_result(result: dict) -> str:
    """
    Turn a Tirith result document into which rule failed, on which resource, and why.

    Use this on the JSON from `tirith --json` or from a CI artefact to explain a red build.

    :param result: A Tirith result document.
    """
    return _json(tools.explain_result(result))


def serve():
    """Run the server on stdio until the client disconnects."""
    mcp.run(transport="stdio")
