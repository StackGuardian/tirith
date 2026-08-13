"""
Argument handling for `tirith ui`, up to but not including starting the interface.

These exercise tui/cli.py's own logic -- path checks, stdin reading, the guards around it --
which is deliberately free of any UI-toolkit import so that a missing optional extra produces
an instruction rather than a traceback. That also means these run on CI's Python 3.8 leg.
"""

import io
import json
import os
import sys

from pytest import importorskip, mark, raises

from tirith import __version__
from tirith.status import ExitStatus
from tirith.tui import cli as ui_cli

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXAMPLE = os.path.join(REPO_ROOT, "src", "tirith", "tui", "examples", "04-block-destroy")


@mark.passing
def test_missing_files_are_reported_before_anything_starts(capsys):
    """A path typo should be a message, not a half-started interface."""
    status = ui_cli.main(["ui", "--result", "/no/such/file.json"])

    assert status == ExitStatus.ERROR
    assert "does not exist" in capsys.readouterr().err


@mark.passing
def test_result_and_policy_are_alternatives(capsys):
    """
    --result opens an evaluation that already happened; --policy opens one to run now. Asking
    for both is a contradiction worth naming rather than resolving by precedence.
    """
    status = ui_cli.main(
        ["ui", "--result", os.path.join(EXAMPLE, "policy.json"), "--policy", os.path.join(EXAMPLE, "policy.json")]
    )

    assert status == ExitStatus.ERROR
    assert "alternatives" in capsys.readouterr().err


@mark.passing
def test_dash_reads_a_document_from_stdin(monkeypatch):
    """
    `tirith --json ... | tirith ui --result -` is the shape people reach for, so '-' has to
    mean stdin rather than a file literally named '-'.
    """
    document = {"evaluators": [], "final_result": True, "errors": []}
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(document)))

    assert ui_cli._load("-", "--result") == document


@mark.passing
def test_empty_stdin_is_reported_clearly(monkeypatch):
    """An empty pipe is usually a failed upstream command; say that rather than 'invalid JSON'."""
    monkeypatch.setattr(sys, "stdin", io.StringIO("   \n"))

    with raises(ValueError) as caught:
        ui_cli._load("-", "--result")

    assert "empty" in str(caught.value)


@mark.passing
def test_broken_stdin_json_names_the_position(monkeypatch):
    """A 200-line plan needs a line and column, not just 'invalid JSON'."""
    monkeypatch.setattr(sys, "stdin", io.StringIO('{"evaluators": ['))

    with raises(ValueError) as caught:
        ui_cli._load("-", "--result")

    message = str(caught.value)
    assert "line" in message and "column" in message


@mark.passing
def test_a_dash_path_skips_the_existence_check(monkeypatch, capsys):
    """
    '-' is not a path, so the existence check must not reject it -- it did, which made the
    whole stdin form unreachable.

    Needs the optional extra: without it `main` reports the missing extra before it reaches
    any of this, which is the correct order -- there is no point reading a document for an
    interface that cannot start.
    """
    importorskip("textual", reason="the TUI is an optional extra")

    monkeypatch.setattr(sys, "stdin", io.StringIO('{"evaluators": [], "errors": []}'))
    # No terminal to hand the interface, so this stops at the tty guard rather than launching.
    monkeypatch.setattr(ui_cli, "_reattach_stdin", lambda: False)

    status = ui_cli.main(["ui", "--result", "-"])

    assert status == ExitStatus.ERROR
    assert "no terminal" in capsys.readouterr().err


@mark.passing
def test_piping_into_serve_is_refused(monkeypatch, capsys):
    """
    The served interface runs as a subprocess with its own stdin, so a document piped to this
    process cannot reach it. Refusing beats serving an empty interface.

    Refused before stdin is read, and before the extra is even looked for, so this holds
    whether or not the interface is installed.
    """
    monkeypatch.setattr(sys, "stdin", io.StringIO('{"evaluators": [], "errors": []}'))

    status = ui_cli.main(["ui", "--result", "-", "--serve"])

    assert status == ExitStatus.ERROR
    assert "stdin" in capsys.readouterr().err


@mark.passing
def test_a_path_that_is_not_a_dash_is_read_from_disk():
    """The ordinary case: `--result some/file.json` reads that file."""
    importorskip("textual", reason="the TUI is an optional extra")

    document = ui_cli._load(os.path.join(EXAMPLE, "policy.json"), "--policy")

    assert document["meta"]["required_provider"] == "stackguardian/terraform_plan"


@mark.passing
def test_an_unreadable_file_is_reported_not_raised(capsys, monkeypatch):
    """
    A directory named where a document was expected, which is what a shell completion of a
    path one level too shallow produces.
    """
    importorskip("textual", reason="the TUI is an optional extra")
    monkeypatch.setattr(ui_cli, "_reattach_stdin", lambda: False)

    status = ui_cli.main(["ui", "--result", EXAMPLE])

    assert status == ExitStatus.ERROR
    assert "ERROR" in capsys.readouterr().err


@mark.passing
def test_the_missing_extra_is_reported_with_instructions(capsys, monkeypatch):
    """
    The expected failure for anyone who installed plain `py-tirith`: an instruction, not an
    ImportError traceback.
    """

    # Setting the module to None makes `from .app import ...` raise ImportError, which is what
    # a missing extra does.
    monkeypatch.setitem(sys.modules, "tirith.tui.app", None)

    status = ui_cli.main(["ui"])

    assert status == ExitStatus.ERROR
    assert "pip install" in capsys.readouterr().err


@mark.passing
def test_the_serve_banner_rows_are_the_same_width():
    """
    The wordmark is drawn by hand, and a row one character short runs one letter into the next
    -- which is exactly what happened: the second T collided with the H, at 21/22/22.

    Compared by width rather than by eye, because that is the property that was actually wrong
    and the one nobody notices by rereading the string literal.
    """
    rows = ui_cli.SERVE_LOGO.split("\n")
    # Strip the markup that opens the first row and the version that closes the last.
    rows[0] = rows[0].replace("[bold cyan]", "")
    rows[2] = rows[2].split("[not bold]")[0]

    widths = {len(row) for row in rows[:3]}
    assert len(widths) == 1, f"rows are ragged: {[len(r) for r in rows[:3]]}"


@mark.passing
def test_the_serve_banner_names_tirith_and_its_version():
    """The banner exists to say what this is; the version is what a reader wants from it."""
    assert __version__ in ui_cli.SERVE_LOGO


@mark.passing
def test_the_served_command_uses_absolute_paths():
    """
    The subprocess does not necessarily inherit this working directory, so a relative --policy
    that resolved here would not resolve there.
    """
    parser = ui_cli.build_parser()
    opts = parser.parse_args(["--policy", "policy.json", "--input", "plan.json"])

    command = ui_cli._rebuild_command(opts, has_result=False)

    assert os.path.isabs(command.split("--policy ")[1].split()[0].strip('"'))
