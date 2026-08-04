"""
Tests for convention-based document discovery and `terraform show -json`.

The property worth protecting hardest is in `test_the_plan_never_reaches_github_output`: calling the
CI wrapper instead of the real binary copies the entire unmasked plan into $GITHUB_OUTPUT, a file
every later step in the job can read.
"""

import json
import os
import stat

import pytest

from tirith.platform import discover
from tirith.platform.discover import DiscoveryError

PLAN = {"format_version": "1.2", "resource_changes": []}


def write(path, content):
    path.write_text(content if isinstance(content, str) else json.dumps(content))
    return path


def fake_binary(directory, name, script):
    """Drop an executable shell script on disk to stand in for terraform."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(script)
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return path


class TestDiscoverInput:
    def test_finds_plan_json(self, tmp_path):
        write(tmp_path / "plan.json", PLAN)
        assert discover.discover_input(str(tmp_path)) == os.path.join(str(tmp_path), "plan.json")

    def test_finds_tfplan_json(self, tmp_path):
        write(tmp_path / "tfplan.json", PLAN)
        assert discover.discover_input(str(tmp_path)) == os.path.join(str(tmp_path), "tfplan.json")

    def test_two_candidates_is_an_error(self, tmp_path):
        """
        Not "first one wins": silently evaluating the wrong document reports a verdict about
        infrastructure the caller did not ask about, and it looks like a pass.
        """
        write(tmp_path / "plan.json", PLAN)
        write(tmp_path / "tfplan.json", PLAN)

        with pytest.raises(DiscoveryError) as excinfo:
            discover.discover_input(str(tmp_path))

        assert "plan.json" in str(excinfo.value)
        assert "tfplan.json" in str(excinfo.value)
        assert "--input-path" in str(excinfo.value)

    def test_no_candidate_names_every_way_out(self, tmp_path):
        with pytest.raises(DiscoveryError) as excinfo:
            discover.discover_input(str(tmp_path))

        message = str(excinfo.value)
        assert "plan.json" in message and "tfplan.json" in message
        assert "--plan-file" in message
        assert "--input-path" in message

    def test_is_not_recursive(self, tmp_path):
        """A plan in a subdirectory belongs to a different unit; picking it up would be wrong."""
        (tmp_path / "modules").mkdir()
        write(tmp_path / "modules" / "plan.json", PLAN)

        with pytest.raises(DiscoveryError):
            discover.discover_input(str(tmp_path))

    def test_ignores_other_json_in_the_directory(self, tmp_path):
        """Two fixed names, not a glob -- a glob would sweep up infracost.json or package.json."""
        write(tmp_path / "infracost.json", {"projects": []})
        write(tmp_path / "package.json", {})

        with pytest.raises(DiscoveryError):
            discover.discover_input(str(tmp_path))

    def test_a_directory_named_plan_json_is_not_a_document(self, tmp_path):
        (tmp_path / "plan.json").mkdir()

        with pytest.raises(DiscoveryError):
            discover.discover_input(str(tmp_path))


class TestResolveBinary:
    def test_prefers_terraform_bin_over_terraform(self, tmp_path, monkeypatch):
        """
        setup-terraform installs a JS wrapper as `terraform` and moves the real binary to
        `terraform-bin`. Calling the wrapper leaks the plan into $GITHUB_OUTPUT.
        """
        bindir = tmp_path / "bin"
        fake_binary(bindir, "terraform", "#!/bin/sh\nexit 0\n")
        fake_binary(bindir, "terraform-bin", "#!/bin/sh\nexit 0\n")
        monkeypatch.setenv("PATH", str(bindir))

        assert os.path.basename(discover._resolve_binary()) == "terraform-bin"

    def test_uses_terraform_cli_path_when_set(self, tmp_path, monkeypatch):
        bindir = tmp_path / "toolcache"
        fake_binary(bindir, "terraform-bin", "#!/bin/sh\nexit 0\n")
        otherdir = tmp_path / "bin"
        fake_binary(otherdir, "terraform", "#!/bin/sh\nexit 0\n")
        monkeypatch.setenv("PATH", str(otherdir))
        monkeypatch.setenv("TERRAFORM_CLI_PATH", str(bindir))

        assert discover._resolve_binary() == str(bindir / "terraform-bin")

    def test_falls_back_to_tofu(self, tmp_path, monkeypatch):
        bindir = tmp_path / "bin"
        fake_binary(bindir, "tofu", "#!/bin/sh\nexit 0\n")
        monkeypatch.setenv("PATH", str(bindir))
        monkeypatch.delenv("TERRAFORM_CLI_PATH", raising=False)
        monkeypatch.delenv("TOFU_CLI_PATH", raising=False)

        assert os.path.basename(discover._resolve_binary()) == "tofu"

    def test_an_explicit_binary_wins(self, tmp_path, monkeypatch):
        bindir = tmp_path / "bin"
        fake_binary(bindir, "terraform-bin", "#!/bin/sh\nexit 0\n")
        monkeypatch.setenv("PATH", str(bindir))

        assert discover._resolve_binary("/opt/custom/tofu") == "/opt/custom/tofu"

    def test_nothing_found_says_what_to_do(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PATH", str(tmp_path / "empty"))
        monkeypatch.delenv("TERRAFORM_CLI_PATH", raising=False)
        monkeypatch.delenv("TOFU_CLI_PATH", raising=False)

        with pytest.raises(DiscoveryError, match="--terraform-bin"):
            discover._resolve_binary()


class TestTerraformShowJson:
    def test_returns_the_parsed_plan(self, tmp_path, monkeypatch):
        bindir = tmp_path / "bin"
        fake_binary(bindir, "terraform-bin", f"#!/bin/sh\necho '{json.dumps(PLAN)}'\n")
        monkeypatch.setenv("PATH", str(bindir))
        plan_file = tmp_path / "tfplan"
        plan_file.write_bytes(b"binary")

        assert discover.terraform_show_json(str(plan_file)) == PLAN

    def test_the_plan_never_reaches_github_output(self, tmp_path, monkeypatch):
        """
        The regression that motivates the whole resolution order. `terraform-bin` is the real
        binary; the `terraform` beside it is the wrapper, which would append the plan to
        $GITHUB_OUTPUT. That file must still be empty afterwards.
        """
        bindir = tmp_path / "bin"
        github_output = tmp_path / "gh_output"
        github_output.write_text("")
        fake_binary(bindir, "terraform-bin", f"#!/bin/sh\necho '{json.dumps(PLAN)}'\n")
        # Stands in for the setup-terraform wrapper: it echoes the plan AND appends it to
        # $GITHUB_OUTPUT, exactly as core.setOutput('stdout', ...) does.
        fake_binary(
            bindir,
            "terraform",
            f"#!/bin/sh\necho 'stdout<<EOF' >> \"$GITHUB_OUTPUT\"\n"
            f"echo '{json.dumps(PLAN)}' >> \"$GITHUB_OUTPUT\"\n"
            f"echo '{json.dumps(PLAN)}'\n",
        )
        monkeypatch.setenv("PATH", str(bindir))
        monkeypatch.setenv("GITHUB_OUTPUT", str(github_output))
        plan_file = tmp_path / "tfplan"
        plan_file.write_bytes(b"binary")

        assert discover.terraform_show_json(str(plan_file)) == PLAN
        assert github_output.read_text() == "", "the wrapper ran and leaked the plan into $GITHUB_OUTPUT"

    def test_invokes_show_json(self, tmp_path, monkeypatch):
        bindir = tmp_path / "bin"
        argv_log = tmp_path / "argv"
        fake_binary(
            bindir,
            "terraform-bin",
            f"#!/bin/sh\necho \"$@\" > '{argv_log}'\necho '{json.dumps(PLAN)}'\n",
        )
        monkeypatch.setenv("PATH", str(bindir))
        plan_file = tmp_path / "tfplan"
        plan_file.write_bytes(b"binary")

        discover.terraform_show_json(str(plan_file))

        assert argv_log.read_text().startswith("show -json ")

    def test_a_wrapper_without_its_real_binary_is_refused(self, tmp_path, monkeypatch):
        """
        TERRAFORM_CLI_PATH set but no terraform-bin anywhere means the only terraform on PATH is the
        wrapper. Refuse rather than leak.
        """
        bindir = tmp_path / "bin"
        fake_binary(bindir, "terraform", "#!/bin/sh\nexit 0\n")
        monkeypatch.setenv("PATH", str(bindir))
        monkeypatch.setenv("TERRAFORM_CLI_PATH", str(tmp_path / "toolcache"))
        monkeypatch.delenv("TOFU_CLI_PATH", raising=False)
        plan_file = tmp_path / "tfplan"
        plan_file.write_bytes(b"binary")

        with pytest.raises(DiscoveryError, match="GITHUB_OUTPUT"):
            discover.terraform_show_json(str(plan_file))

    def test_a_failure_surfaces_stderr(self, tmp_path, monkeypatch):
        bindir = tmp_path / "bin"
        fake_binary(bindir, "terraform-bin", '#!/bin/sh\necho "Saved plan is stale" >&2\nexit 1\n')
        monkeypatch.setenv("PATH", str(bindir))
        plan_file = tmp_path / "tfplan"
        plan_file.write_bytes(b"binary")

        with pytest.raises(DiscoveryError, match="Saved plan is stale"):
            discover.terraform_show_json(str(plan_file))

    def test_non_json_output_does_not_echo_stdout(self, tmp_path, monkeypatch):
        """On the wrapper path stdout would be the whole plan, so it must never reach the log."""
        bindir = tmp_path / "bin"
        fake_binary(bindir, "terraform-bin", '#!/bin/sh\necho "AKIAIOSFODNN7EXAMPLE not json"\n')
        monkeypatch.setenv("PATH", str(bindir))
        plan_file = tmp_path / "tfplan"
        plan_file.write_bytes(b"binary")

        with pytest.raises(DiscoveryError) as excinfo:
            discover.terraform_show_json(str(plan_file))

        assert "AKIAIOSFODNN7EXAMPLE" not in str(excinfo.value)
