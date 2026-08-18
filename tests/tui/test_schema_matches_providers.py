"""
The TUI's hand-written provider table must describe the providers that actually exist.

src/tirith/tui/schema.py cannot be derived from the engine -- terraform_plan dispatches through
an if/elif chain and sg_workflow has no operation_type at all -- so it is written by hand, and a
hand-written copy of someone else's structure rots. These tests are the thing that stops it:
add an operation to a provider without describing it here and CI goes red, which is the same
guardrail tests/test_readme_is_current.py puts on the README.

Deliberately no textual import anywhere in this file. CI runs the suite on Python 3.8, where
textual cannot be installed, so schema.py is kept free of TUI imports and these run everywhere.
"""

import ast
import os

from pytest import mark

from tirith.providers import PROVIDERS_DICT
from tirith.core.evaluators import EVALUATORS_DICT
from tirith.tui import schema

PROVIDER_SRC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "src",
    "tirith",
    "providers",
)


def _handler_source(provider_dirname):
    with open(os.path.join(PROVIDER_SRC_DIR, provider_dirname, "handler.py")) as f:
        return f.read()


def _string_constants(source):
    """Every string literal in a module, which is where operation names live either way."""
    return {
        node.value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


# The directory each provider's handler lives in, keyed by the name policies use.
_DIRNAMES = {
    "stackguardian/terraform_plan": "terraform_plan",
    "stackguardian/json": "json",
    "stackguardian/kubernetes": "kubernetes",
    "stackguardian/infracost": "infracost",
    "stackguardian/sg_workflow": "sg_workflow",
}


@mark.passing
def test_every_described_provider_is_registered():
    """A provider named in the table must be one the engine can actually dispatch to."""
    assert set(schema.PROVIDERS) == set(PROVIDERS_DICT), (
        "tui/schema.py PROVIDERS has drifted from providers/__init__.py PROVIDERS_DICT. "
        "Add or remove the provider in the table to match."
    )


@mark.passing
def test_every_described_operation_appears_in_its_handler():
    """
    Each operation_type in the table must appear literally in the provider's handler.

    A string match rather than a call, because the handlers disagree on how they dispatch:
    json and kubernetes use a SUPPORTED_OPS dict, terraform_plan an if/elif chain, infracost a
    lookup table keyed by the operation name. The one thing all three share is that the name
    appears as a literal in the module. That makes this a check against typos and removals --
    the drift that actually happens -- and not a proof the operation behaves as described.
    """
    for provider_name, provider in schema.PROVIDERS.items():
        if not provider.uses_operation_type:
            continue
        literals = _string_constants(_handler_source(_DIRNAMES[provider_name]))
        for operation in provider.operations:
            assert operation.name in literals, (
                f"tui/schema.py describes operation '{operation.name}' for {provider_name}, "
                f"but that string does not appear in its handler. Renamed or removed?"
            )


@mark.passing
def test_described_args_appear_in_their_handler():
    """
    Each argument name in the table must be one its handler actually reads.

    Same literal-match reasoning as the operations check above: the handlers read arguments by
    subscript and by .get(), so the name appears as a literal either way. This catches the
    failure the table exists to prevent -- the builder generating `terraform_resource_attr`
    against a provider that reads `terraform_resource_attribute`, producing a policy that
    parses fine and silently finds nothing.
    """
    for provider_name, provider in schema.PROVIDERS.items():
        literals = _string_constants(_handler_source(_DIRNAMES[provider_name]))
        for operation in provider.operations:
            for arg in operation.args:
                assert arg.name in literals, (
                    f"tui/schema.py describes argument '{arg.name}' for "
                    f"{provider_name}.{operation.name}, but no such string appears in its handler."
                )


@mark.passing
def test_terraform_operations_that_honour_exclude_resource_types_all_declare_it():
    """
    The reverse direction: handler -> table.

    Every other check here asks whether what the table describes exists. Nothing asked whether
    what the handler *reads* is described, which is how exclude_resource_types came to be
    attached to `attribute` alone while provide() honours it in three branches -- so the
    validator reported a correct `count` policy as using an ignored argument.

    Counted from the source: each branch that consults the name needs it in the table.
    """
    # Code lines only: each branch carries a comment naming the argument as well, so counting
    # every mention doubles the real figure.
    source = _handler_source("terraform_plan")
    honouring = sum(
        1 for line in source.splitlines() if "in exclude_resource_types" in line and not line.strip().startswith("#")
    )

    declared = [
        operation.name
        for operation in schema.PROVIDERS["stackguardian/terraform_plan"].operations
        if any(arg.name == "exclude_resource_types" for arg in operation.args)
    ]

    assert len(declared) == honouring, (
        f"terraform_plan consults exclude_resource_types in {honouring} branches but the table "
        f"declares it for {len(declared)}: {declared}. A policy using it on an undeclared "
        f"operation is reported as ignoring the argument, which is wrong."
    )


@mark.passing
def test_sg_workflow_attribute_choices_are_all_handled():
    """
    sg_workflow raises KeyError on an attribute it does not branch on, so offering one that is
    not handled would build a policy that always errors. Every choice must be a real branch.
    """
    literals = _string_constants(_handler_source("sg_workflow"))
    (operation,) = schema.PROVIDERS["stackguardian/sg_workflow"].operations
    (attribute_arg,) = operation.args
    for choice in attribute_arg.choices:
        assert choice in literals, f"sg_workflow attribute '{choice}' is offered but never handled."


@mark.passing
def test_every_described_evaluator_is_registered():
    assert set(schema.EVALUATORS) == set(
        EVALUATORS_DICT
    ), "tui/schema.py EVALUATORS has drifted from core/evaluators/__init__.py EVALUATORS_DICT."


@mark.passing
def test_value_kinds_are_known():
    """value_kind steers which widget the builder shows, so a typo would silently degrade the form."""
    for info in schema.EVALUATORS.values():
        assert info.value_kind in (
            "scalar",
            "list",
            "none",
            "regex",
        ), f"{info.name} declares unknown value_kind '{info.value_kind}'"
