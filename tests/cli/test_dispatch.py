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
    """
    Only names in SUBCOMMANDS dispatch; anything else goes to the flat parser.

    `check` in particular must stay out: making it a top-level verb would mean the policy *source*
    depended on whether SG_API_TOKEN happened to be exported, so an ambient environment variable could
    silently swap local policy files for an organization's enforced set.
    """
    assert cli.SUBCOMMAND == "platform"
    assert "platform" in cli.SUBCOMMANDS
    assert "check" not in cli.SUBCOMMANDS


def test_the_subcommand_names_are_exactly_these(capsys):
    """
    `platform` was briefly renamed to `remote` and then reverted. Neither direction kept an alias --
    nothing is released, so there was never a caller to keep working -- and this pins the outcome:
    `remote` is not quietly still accepted.

    `ui` was added alongside it later, on the same terms: dispatched before the flat parser so the
    local surface and its golden-file output are untouched. `mcp` joined them on those same terms.
    The set is pinned rather than merely checked for membership, so a new subcommand has to be a
    deliberate edit here.
    """
    assert cli.SUBCOMMANDS == {"platform", "ui", "mcp"}

    status = cli.main(["remote"])

    assert status != ExitStatus.SUCCESS
    assert "tirith platform" not in capsys.readouterr().out


def test_ui_dispatches_to_its_own_parser(capsys):
    """
    `ui` must reach its own parser rather than the flat one, which would reject it for having no
    -policy-path.

    Asserted through a bad flag, so the interface itself never starts and this stays runnable
    without the optional extra installed. argparse exits rather than returning on an unknown
    flag -- the same thing `tirith platform --nope` does -- so the SystemExit is the pass
    condition; what matters is *which* parser produced the complaint.
    """
    with pytest.raises(SystemExit):
        cli.main(["ui", "--no-such-flag"])

    error = capsys.readouterr().err
    assert "tirith ui" in error, error
    assert "-policy-path" not in error


def test_mcp_dispatches_to_its_own_parser(capsys):
    """
    `mcp` must reach its own parser rather than the flat one, which would reject it for having no
    -policy-path.

    Asserted through a bad flag, so the server never starts and this stays runnable without the
    optional extra installed -- the same shape as the `ui` test above, and for the same reason:
    the commonest state of a machine running this test is not having the extra.
    """
    with pytest.raises(SystemExit):
        cli.main(["mcp", "--nope"])

    assert "tirith mcp" in capsys.readouterr().err


def test_mcp_without_the_extra_reports_the_extra(capsys):
    """
    Missing optional dependency is a message, not a traceback.

    `tirith mcp` on a machine without the SDK is the commonest way to reach that code path, and
    an ImportError stack there tells the reader nothing about what to install.
    """
    import tirith.mcp.cli as mcp_cli

    try:
        import mcp  # noqa: F401
    except ImportError:
        pass
    else:
        pytest.skip("the mcp extra is installed, so the missing-extra path cannot be exercised")

    status = mcp_cli.main(["mcp"])

    assert status == ExitStatus.ERROR
    assert "'mcp' extra" in capsys.readouterr().err
