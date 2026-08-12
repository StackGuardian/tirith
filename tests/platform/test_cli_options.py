"""
Tests for `tirith remote check` option handling.

Everything here is asserted *before* any HTTP call, which is the point: a bad workflow id or a
contradictory pair of URL flags should fail immediately rather than after a run has been created.
"""

import json

import pytest

from tirith.platform import cli
from tirith.status import ExitStatus

PLAN = {"format_version": "1.2", "resource_changes": []}

# The minimum run_check result cli.main will accept without reaching for a missing key.
PASSED = {"verdict": "passed", "counts": {}, "policies": {}}


@pytest.fixture
def no_network(monkeypatch):
    """Make any attempt to reach the platform an outright test failure."""

    def explode(*a, **kw):
        raise AssertionError("run_check was called; the option check should have failed first")

    monkeypatch.setattr(cli, "run_check", explode)


def base_args(tmp_path, *extra):
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps(PLAN))
    return ["remote", "check", "--input-path", str(plan), *extra]


def env(monkeypatch, **values):
    for key in ("SG_API_TOKEN", "SG_ORG", "SG_BASE_URL", "SG_DASHBOARD_URL", "SG_REGION"):
        monkeypatch.delenv(key, raising=False)
    for key, value in values.items():
        monkeypatch.setenv(key, value)


class TestWorkflowIdValidation:
    @pytest.mark.parametrize("workflow_id", ["live/prod/vpc", "has.dots", "a" * 101, "spaces here", ""])
    def test_a_bad_slug_is_refused_before_any_request(self, workflow_id, tmp_path, monkeypatch, no_network, capsys):
        """
        The value is interpolated into every API path and the platform's own field is a slug, so a
        '/' produces a malformed URL rather than a clear error.
        """
        env(monkeypatch, SG_API_TOKEN="sgo_x", SG_ORG="acme")

        status = cli.main(base_args(tmp_path, "--workflow-id", workflow_id))

        assert status == ExitStatus.ERROR
        assert "not a valid slug" in capsys.readouterr().err

    def test_the_error_suggests_a_usable_slug(self, tmp_path, monkeypatch, no_network, capsys):
        env(monkeypatch, SG_API_TOKEN="sgo_x", SG_ORG="acme")

        cli.main(base_args(tmp_path, "--workflow-id", "live/prod/vpc"))

        assert "live-prod-vpc" in capsys.readouterr().err

    @pytest.mark.parametrize("workflow_id", ["github-com-acme-infra-plan", "a_b-C9", "x"])
    def test_valid_slugs_pass(self, workflow_id, tmp_path, monkeypatch, capsys):
        env(monkeypatch, SG_API_TOKEN="sgo_x", SG_ORG="acme")
        seen = {}

        def capture(opts):
            seen["workflow_id"] = opts.workflow_id
            return PASSED

        monkeypatch.setattr(cli, "run_check", capture)
        cli.main(base_args(tmp_path, "--workflow-id", workflow_id))

        assert seen["workflow_id"] == workflow_id


class TestRegionResolution:
    def resolved(self, tmp_path, monkeypatch, *extra):
        seen = {}

        def capture(opts):
            seen["api_url"] = opts.api_url
            seen["dashboard_url"] = opts.dashboard_url
            return PASSED

        monkeypatch.setattr(cli, "run_check", capture)
        status = cli.main(base_args(tmp_path, "--workflow-id", "wf", *extra))
        return status, seen

    def test_region_us_sets_both_urls(self, tmp_path, monkeypatch):
        env(monkeypatch, SG_API_TOKEN="sgo_x", SG_ORG="acme")

        _status, seen = self.resolved(tmp_path, monkeypatch, "--region", "us")

        assert seen["api_url"] == "https://api.us.stackguardian.io/api/v1"
        assert seen["dashboard_url"] == "https://us.stackguardian.io"

    def test_defaults_to_eu(self, tmp_path, monkeypatch):
        env(monkeypatch, SG_API_TOKEN="sgo_x", SG_ORG="acme")

        _status, seen = self.resolved(tmp_path, monkeypatch)

        assert seen["api_url"] == "https://api.app.stackguardian.io/api/v1"
        assert seen["dashboard_url"] == "https://app.stackguardian.io"

    def test_region_with_an_explicit_url_fails_before_any_request(self, tmp_path, monkeypatch, no_network, capsys):
        env(monkeypatch, SG_API_TOKEN="sgo_x", SG_ORG="acme")

        status = cli.main(
            base_args(tmp_path, "--workflow-id", "wf", "--region", "us", "--api-url", "https://x.example")
        )

        assert status == ExitStatus.ERROR
        assert "cannot be combined" in capsys.readouterr().err

    def test_an_unknown_region_is_rejected_by_the_parser(self, tmp_path, monkeypatch):
        env(monkeypatch, SG_API_TOKEN="sgo_x", SG_ORG="acme")

        with pytest.raises(SystemExit):
            cli.main(base_args(tmp_path, "--workflow-id", "wf", "--region", "uss"))

    def test_a_base_url_without_the_api_path_still_works(self, tmp_path, monkeypatch):
        """A SG_BASE_URL exported for sg-cli omits /api/v1 and used to 404 here."""
        env(monkeypatch, SG_API_TOKEN="sgo_x", SG_ORG="acme", SG_BASE_URL="https://api.us.stackguardian.io")

        _status, seen = self.resolved(tmp_path, monkeypatch)

        assert seen["api_url"] == "https://api.us.stackguardian.io/api/v1"

    def test_setting_only_the_api_url_still_gets_correct_run_links(self, tmp_path, monkeypatch):
        """The original footgun: run links pointed at the EU dashboard for a US org."""
        env(monkeypatch, SG_API_TOKEN="sgo_x", SG_ORG="acme")

        _status, seen = self.resolved(tmp_path, monkeypatch, "--api-url", "https://api.us.stackguardian.io")

        assert seen["dashboard_url"] == "https://us.stackguardian.io"


class TestDocumentSelection:
    def test_a_plan_is_discovered_when_nothing_is_named(self, tmp_path, monkeypatch):
        (tmp_path / "plan.json").write_text(json.dumps(PLAN))
        env(monkeypatch, SG_API_TOKEN="sgo_x", SG_ORG="acme")
        seen = {}
        monkeypatch.setattr(cli, "run_check", lambda opts: seen.update(input_path=opts.input_path) or PASSED)

        cli.main(["remote", "check", "--workflow-id", "wf", "--source-dir", str(tmp_path)])

        assert seen["input_path"].endswith("plan.json")

    def test_nothing_to_evaluate_is_an_error(self, tmp_path, monkeypatch, no_network, capsys):
        env(monkeypatch, SG_API_TOKEN="sgo_x", SG_ORG="acme")

        status = cli.main(["remote", "check", "--workflow-id", "wf", "--source-dir", str(tmp_path)])

        assert status == ExitStatus.ERROR
        assert "No plan document found" in capsys.readouterr().err

    def test_plan_file_and_input_path_cannot_be_combined(self, tmp_path, monkeypatch, no_network, capsys):
        env(monkeypatch, SG_API_TOKEN="sgo_x", SG_ORG="acme")

        status = cli.main(base_args(tmp_path, "--workflow-id", "wf", "--plan-file", str(tmp_path / "tfplan")))

        assert status == ExitStatus.ERROR
        assert "cannot be combined" in capsys.readouterr().err

    def test_an_explicit_input_path_skips_discovery(self, tmp_path, monkeypatch):
        """Two candidates would be ambiguous for discovery, but naming one is unambiguous."""
        (tmp_path / "plan.json").write_text(json.dumps(PLAN))
        (tmp_path / "tfplan.json").write_text(json.dumps(PLAN))
        env(monkeypatch, SG_API_TOKEN="sgo_x", SG_ORG="acme")
        seen = {}
        monkeypatch.setattr(cli, "run_check", lambda opts: seen.update(input_path=opts.input_path) or PASSED)

        status = cli.main(
            [
                "remote",
                "check",
                "--workflow-id",
                "wf",
                "--source-dir",
                str(tmp_path),
                "--input-path",
                str(tmp_path / "tfplan.json"),
            ]
        )

        assert status != ExitStatus.ERROR
        assert seen["input_path"].endswith("tfplan.json")


class TestCredentials:
    def test_credentials_come_from_the_environment(self, tmp_path, monkeypatch):
        """
        The one-liner needs this: GitHub exposes neither secrets nor vars as env automatically, so
        an `env:` block is the only no-`with:` route.
        """
        env(monkeypatch, SG_API_TOKEN="sgo_fromenv", SG_ORG="acme-from-env")
        seen = {}
        monkeypatch.setattr(cli, "run_check", lambda opts: seen.update(api_key=opts.api_key, org=opts.org) or PASSED)

        cli.main(base_args(tmp_path, "--workflow-id", "wf"))

        assert seen == {"api_key": "sgo_fromenv", "org": "acme-from-env"}

    def test_missing_credentials_name_both(self, tmp_path, monkeypatch, no_network, capsys):
        env(monkeypatch)

        status = cli.main(base_args(tmp_path, "--workflow-id", "wf"))

        assert status == ExitStatus.ERROR
        err = capsys.readouterr().err
        assert "--api-key" in err and "--org" in err
