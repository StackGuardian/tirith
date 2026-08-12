"""
The README's generated bits must match what the program actually prints.

Three things in it were hand-copied and had gone stale: the `## Usage` block was a paste of an older
`--help` missing `-var-path`, `-var` and the whole `platform` subcommand; the install-verification step
showed `1.0.0-beta.12` against a shipped `1.2.0`; and the Getting Started sample output predated the
current message format, so the first command a new user runs printed something different from the
documentation.

Correcting the text is a one-off; it had already been corrected before and rotted again. What stops
that is checking it, so these run in CI. They compare against the real program output rather than
against a golden file, so adding a flag updates the requirement automatically -- the README is what has
to move.
"""

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
README = os.path.join(ROOT, "README.md")

sys.path.insert(0, SRC)

from tirith import __version__


def _readme():
    with open(README) as f:
        return f.read()


def _help(*args):
    """Run the CLI's --help the way a user would, in a subprocess, not by calling into argparse."""
    argv = list(args) + ["--help"]
    code = (
        "import sys\n"
        f"sys.argv = ['tirith'] + {argv!r}\n"
        "from tirith.cli import main\n"
        "try:\n"
        "    main()\n"
        "except SystemExit:\n"
        "    pass\n"
    )
    env = dict(os.environ, PYTHONPATH=SRC)
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env).stdout


def _fenced_block_after(heading):
    text = _readme()
    start = text.index(heading) + len(heading)
    open_fence = text.index("```", start)
    close_fence = text.index("```", open_fence + 3)
    return text[open_fence + 3 : close_fence].strip("\n")


def _options(text):
    """Every option string in a help text, e.g. `{-policy-path, --json, --fail-on-error}`."""
    return set(re.findall(r"(?<![\w-])(--?[a-z][\w-]*)", text))


def test_the_usage_block_lists_every_option_the_cli_accepts():
    """
    A pasted `--help` is stale as soon as a flag is added, and two were: `-var-path` and `-var`,
    which are the whole policy-parameterization feature.

    Compares the *set of options* rather than the text byte for byte. Byte equality looked stronger and
    was unusable: argparse renamed its section header from "optional arguments:" to "options:" in 3.10,
    so a block generated on any one interpreter fails on the other half of the CI matrix -- which is
    exactly how this test failed on 3.8 and 3.9 while passing on 3.10 through 3.12. The version-portable
    part is the thing worth pinning anyway: a flag that exists and is undocumented, or documented and
    gone.
    """
    documented = _options(_fenced_block_after("## Usage"))
    actual = _options(_help())

    undocumented = sorted(actual - documented)
    phantom = sorted(documented - actual)

    assert not undocumented, f"accepted by the CLI but absent from the README's Usage block: {undocumented}"
    assert not phantom, f"documented in the Usage block but not accepted by the CLI: {phantom}"


def test_the_version_shown_in_the_install_steps_is_the_shipped_one():
    """The last step of the install instructions is a command whose output is documented."""
    assert f"tirith {__version__}" in _readme(), (
        f"the README does not show `tirith {__version__}`; the install verification step "
        "documents a version that is no longer shipped"
    )


def test_the_platform_subcommand_is_documented():
    """
    It is dispatched before argparse sees anything (`cli.py`, SUBCOMMANDS), so it cannot appear in the
    top-level usage line automatically -- which is exactly how it stayed undocumented while being the
    reason the branch exists.
    """
    text = _readme()
    assert "tirith platform check" in text
    assert "SG_API_TOKEN" in text and "SG_ORG" in text, "the credentials it needs are not named"
    assert os.path.exists(os.path.join(ROOT, "docs", "platform-check.md")), "the reference page is linked but missing"


def test_the_flag_reference_page_lists_every_flag_the_command_accepts():
    """
    docs/platform-check.md embeds the full `--help`. A flag added without touching it silently stops
    being documented, which is how a 25-flag surface ends up with a partial reference.
    """
    with open(os.path.join(ROOT, "docs", "platform-check.md")) as f:
        page = f.read()

    flags = set(re.findall(r"(?<![\w-])--[a-z][a-z0-9-]+", _help("platform", "check")))
    missing = sorted(f for f in flags if f not in page)

    assert not missing, f"flags accepted by `platform check` but absent from docs/platform-check.md: {missing}"


def test_the_documented_exit_codes_are_the_real_ones():
    """
    The reason to document them at all is that 3 is not 1 -- "a policy said no" versus "could not
    tell you". A table that drifts from the enum is worse than none, because CI is written against it.
    """
    from tirith.status import ExitStatus

    text = _readme()
    assert "## Exit codes" in text
    table = text.split("## Exit codes", 1)[1].split("##", 1)[0]

    for status in ExitStatus:
        assert f"| {status.value} |" in table, f"{status.name} ({status.value}) is not in the exit-code table"
