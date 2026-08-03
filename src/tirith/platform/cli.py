"""
`tirith platform ...` -- run policy checks against a StackGuardian organization.

Flag and environment names follow sg-cli (SG_API_TOKEN, SG_BASE_URL, SG_ORG, SG_DASHBOARD_URL) so
someone who knows one tool knows the other.
"""

import argparse
import json
import os
import sys

from ..status import ExitStatus
from .check import DEFAULT_WORKFLOW_GROUP, INPUT_KINDS, CheckError, log, run_check

DEFAULT_API_URL = "https://api.app.stackguardian.io/api/v1"
DEFAULT_DASHBOARD_URL = "https://app.stackguardian.io"


def _resolve_api_key(value):
    """
    Resolve the API key, preferring the environment.

    A key on argv is visible in `ps` for the lifetime of the process, so `-` reads it from stdin
    and $SG_API_TOKEN is the documented default.
    """
    if value == "-":
        return sys.stdin.readline().strip()
    return value or os.environ.get("SG_API_TOKEN", "")


def _load_trigger_details(opts):
    if opts.trigger_details_json:
        source, raw = "--trigger-details-json", opts.trigger_details_json
    elif opts.trigger_details_file:
        source = f"--trigger-details-file {opts.trigger_details_file}"
        try:
            with open(opts.trigger_details_file) as f:
                raw = f.read()
        except OSError as e:
            raise CheckError(f"Could not read {opts.trigger_details_file}: {e}")
    else:
        return {"type": "cli"}

    try:
        details = json.loads(raw)
    except json.JSONDecodeError as e:
        raise CheckError(f"{source} is not valid JSON: {e}")
    if not isinstance(details, dict):
        raise CheckError(f"{source} must be a JSON object")
    details.setdefault("type", "cli")
    return details


def build_parser():
    parser = argparse.ArgumentParser(
        prog="tirith platform",
        description="Run StackGuardian policy checks from a CI pipeline or a laptop.",
    )
    sub = parser.add_subparsers(dest="subcommand")

    check = sub.add_parser(
        "check",
        help="Evaluate the organization's policies against a document and report the verdict.",
        description=(
            "Masks the document, packs it with the terraform source into an archive, uploads it, "
            "runs the policies on StackGuardian and reports the verdict."
        ),
    )

    identity = check.add_argument_group("identity")
    identity.add_argument(
        "--api-key", default=None, help="API key, or '-' to read it from stdin. Default: $SG_API_TOKEN"
    )
    identity.add_argument("--org", default=None, help="Organization name. Default: $SG_ORG")
    identity.add_argument("--api-url", default=None, help=f"API base URL. Default: $SG_BASE_URL or {DEFAULT_API_URL}")
    identity.add_argument("--dashboard-url", default=None, help="Dashboard base URL, used to build run links.")

    workflow = check.add_argument_group("workflow")
    workflow.add_argument("--workflow-id", required=True, help="Slug identifying the workflow. Created if absent.")
    workflow.add_argument("--workflow-group", default=DEFAULT_WORKFLOW_GROUP, help="Workflow group. Created if absent.")
    workflow.add_argument("--terraform-version", default=None, help="Stored on the workflow at creation.")
    workflow.add_argument(
        "--step-template-id",
        default=None,
        help="Override the terraform step template. Omit to use the platform's own default.",
    )

    inputs = check.add_argument_group("inputs")
    inputs.add_argument("--input-path", default=None, help="Document to evaluate, e.g. `terraform show -json tfplan`.")
    inputs.add_argument("--input-kind", default="terraform_plan", choices=INPUT_KINDS)
    inputs.add_argument("--state-path", default=None, help="Optional terraform state, masked before upload.")
    inputs.add_argument("--infracost-path", default=None, help="Optional `infracost breakdown --format json`.")
    inputs.add_argument("--source-dir", default=".", help="Terraform source to pack alongside the documents.")
    inputs.add_argument("--no-source", action="store_true", help="Send only the documents, not the source tree.")

    run = check.add_argument_group("run")
    run.add_argument("--sha", default=None, help="Commit SHA, used to namespace the uploaded archive.")
    run.add_argument("--artifact-tag", default="default", help="Namespaces the archive within a commit.")
    run.add_argument("--trigger-details-json", default=None, help="JSON object describing what triggered this run.")
    run.add_argument("--trigger-details-file", default=None, help="File containing that JSON object.")
    run.add_argument("--timeout", type=int, default=1800, help="Seconds to wait for the run. Default: 1800")

    output = check.add_argument_group("output")
    output.add_argument("--output-json", default=None, help="Write the result document here.")
    output.add_argument("--output-markdown", default=None, help="Write a markdown report here.")
    output.add_argument("--comment-marker", default=None, help="Opaque first line of the markdown, for stickiness.")
    output.add_argument("--markdown-limit", type=int, default=60000, help="Truncate the markdown to this length.")
    output.add_argument(
        "--fail-on-error",
        action="store_true",
        help=(
            "Exit non-zero when a policy fails. An unreachable platform or a run that produced no "
            "verdict always exits non-zero regardless of this flag."
        ),
    )

    return parser


def main(argv):
    parser = build_parser()
    opts = parser.parse_args(argv[1:])

    if opts.subcommand != "check":
        parser.print_help()
        return ExitStatus.SUCCESS

    opts.api_key = _resolve_api_key(opts.api_key)
    opts.org = opts.org or os.environ.get("SG_ORG", "")
    opts.api_url = opts.api_url or os.environ.get("SG_BASE_URL") or DEFAULT_API_URL
    opts.dashboard_url = opts.dashboard_url or os.environ.get("SG_DASHBOARD_URL") or DEFAULT_DASHBOARD_URL
    opts.source_dir = None if opts.no_source else opts.source_dir

    missing = [name for name, value in (("--api-key", opts.api_key), ("--org", opts.org)) if not value]
    if missing:
        log(f"ERROR: missing required {' and '.join(missing)}")
        return ExitStatus.ERROR

    if not opts.input_path and not opts.state_path:
        log("ERROR: at least one of --input-path or --state-path is required")
        return ExitStatus.ERROR

    if opts.api_key.startswith("sgu_"):
        log(
            "WARNING: sgu_ tokens are non-functional for SSO-group-only users and inherit only "
            "direct permissions for hybrid SSO users. Prefer an organization (sgo_) token."
        )

    try:
        opts.trigger_details = _load_trigger_details(opts)
        result = run_check(opts)
    except CheckError as e:
        # Fails closed: a run that produced no verdict must never look like a pass, whatever
        # --fail-on-error says.
        log(f"ERROR: {e}")
        return ExitStatus.ERROR
    except KeyboardInterrupt:
        log("Interrupted")
        return ExitStatus.ERROR_CTRL_C

    verdict = result["verdict"]
    if verdict == "errored":
        # Fails closed regardless of --fail-on-error: the flag governs policy verdicts, not tool
        # health, and a run that produced no verdict must never look like a pass.
        log("The run did not produce a verdict")
        return ExitStatus.ERROR
    if verdict in ("failed", "approval-required") and opts.fail_on_error:
        return ExitStatus.ERROR_POLICY_FAILED
    if verdict == "failed":
        log("Policies failed, but --fail-on-error was not set")
    if verdict == "approval-required":
        log("The run is waiting for approval; --fail-on-error was not set")

    return ExitStatus.SUCCESS
