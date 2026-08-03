"""
Tests for subcommand dispatch.

The local-evaluation surface is a contract: the platform and the workflow-step templates parse its
--json output, and tests/core/test_output_compatibility.py asserts that output byte-for-byte.
Adding `tirith platform` must leave it completely untouched, including its single-dash long
options, which argparse cannot express alongside a subparser.
"""

import json
import os

import pytest

from tirith import cli
from tirith.status import ExitStatus

FIXTURES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "providers", "json")
POLICY = os.path.join(FIXTURES, "policy.json")
INPUT = os.path.join(FIXTURES, "input.json")


def test_legacy_invocation_still_works(capsys):
    """The flat parser must keep working exactly as before, driven through main(args=...)."""
    status = cli.main(["-policy-path", POLICY, "-input-path", INPUT, "--json"])

    assert status == ExitStatus.SUCCESS
    document = json.loads(capsys.readouterr().out)
    assert "final_result" in document
    assert "evaluators" in document


def test_main_honours_its_args_parameter(capsys):
    """
    It did not before: parse_args() was called with no argument, so main(args=...) was ignored and
    the CLI always read sys.argv. That made it untestable and undrivable from another program.
    """
    status = cli.main(["-policy-path", POLICY, "-input-path", INPUT, "--json"])

    assert status == ExitStatus.SUCCESS
    assert capsys.readouterr().out.strip().startswith("{")


def test_no_arguments_prints_help(capsys):
    """
    Pre-existing behaviour, asserted so the dispatcher does not change it: the sys.exit(0) is
    caught by main's own SystemExit handler, which returns None for a zero code. __main__ treats
    that as success.
    """
    status = cli.main([])

    assert not status
    assert "usage" in capsys.readouterr().out.lower()


def test_platform_is_dispatched_to_the_subcommand(capsys):
    """`platform` with no subcommand prints the platform help, not the local-evaluation help."""
    status = cli.main(["platform"])

    assert status == ExitStatus.SUCCESS
    assert "tirith platform" in capsys.readouterr().out


def test_platform_check_requires_credentials(capsys, monkeypatch):
    monkeypatch.delenv("SG_API_TOKEN", raising=False)
    monkeypatch.delenv("SG_ORG", raising=False)

    status = cli.main(["platform", "check", "--workflow-id", "wf", "--input-path", INPUT])

    assert status == ExitStatus.ERROR
    assert "--api-key" in capsys.readouterr().err


def test_platform_check_requires_a_document(capsys, monkeypatch):
    monkeypatch.setenv("SG_API_TOKEN", "sgo_x")
    monkeypatch.setenv("SG_ORG", "acme")

    status = cli.main(["platform", "check", "--workflow-id", "wf"])

    assert status == ExitStatus.ERROR
    assert "--input-path" in capsys.readouterr().err


def test_a_bare_word_is_not_mistaken_for_a_subcommand(capsys):
    """Only names in SUBCOMMANDS dispatch; anything else goes to the flat parser."""
    assert "platform" in cli.SUBCOMMANDS
    assert "check" not in cli.SUBCOMMANDS
