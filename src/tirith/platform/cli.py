"""
`tirith platform ...` -- run policy checks against a StackGuardian organization.

Flag and environment names follow sg-cli (SG_API_TOKEN, SG_BASE_URL, SG_ORG, SG_DASHBOARD_URL) so
someone who knows one tool knows the other. `--region` names both URLs at once; see regions.py for
the precedence between it, the explicit flags and the environment.
"""

import argparse
import json
import os
import re
import sys

from ..status import ExitStatus
from . import discover, regions
from .check import DEFAULT_WORKFLOW_GROUP, INPUT_KINDS, CheckError, log, run_check

# `Id` is a DRF SlugField on the platform, and the value is interpolated into every API path.
WORKFLOW_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,100}$")


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
    identity.add_argument(
        "--region",
        default=None,
        choices=regions.REGION_IDS,
        help=(
            f"StackGuardian region, setting both URLs at once. " f"Default: $SG_REGION or {regions.DEFAULT_REGION_ID}."
        ),
    )
    identity.add_argument(
        "--api-url",
        default=None,
        help=(
            "API base URL, with or without /api/v1. Overrides --region; needed only for a "
            "self-hosted install or a dedicated host. Default: $SG_BASE_URL"
        ),
    )
    identity.add_argument(
        "--dashboard-url",
        default=None,
        help="Dashboard base URL, used to build run links. Inferred from --api-url when it names a known region.",
    )

    workflow = check.add_argument_group("workflow")
    workflow.add_argument(
        "--workflow-id",
        required=True,
        help="Slug identifying the workflow. Created if absent. Letters, digits, '-' and '_' only.",
    )
    workflow.add_argument("--workflow-group", default=DEFAULT_WORKFLOW_GROUP, help="Workflow group. Created if absent.")
    workflow.add_argument("--terraform-version", default=None, help="Stored on the workflow at creation.")
    workflow.add_argument(
        "--repo-url",
        default=None,
        help="Source repository URL, recorded on the workflow at creation so it links back to the code.",
    )
    workflow.add_argument("--repo-ref", default=None, help="Branch, tag or commit, recorded alongside --repo-url.")
    workflow.add_argument(
        "--step-template-id",
        default=None,
        help="Override the policy-evaluation step template. Omit to use the platform's own default.",
    )

    inputs = check.add_argument_group("inputs")
    inputs.add_argument(
        "--input-path",
        default=None,
        help=(
            "Document to evaluate. Defaults to whichever of "
            f"{' or '.join(discover.PLAN_FILENAMES)} is in --source-dir."
        ),
    )
    inputs.add_argument(
        "--plan-file",
        default=None,
        help=(
            "Binary plan from `terraform plan -out=`. Rendered with `show -json` in memory, so no "
            "unmasked plan JSON is written to disk. Use --input-path if you already have the JSON."
        ),
    )
    inputs.add_argument(
        "--terraform-bin",
        default=None,
        help="terraform/tofu binary for --plan-file. Auto-detected, preferring the real binary over a CI wrapper.",
    )
    inputs.add_argument("--input-kind", default="terraform_plan", choices=INPUT_KINDS)
    inputs.add_argument("--state-path", default=None, help="Optional terraform state, masked before upload.")
    inputs.add_argument("--infracost-path", default=None, help="Optional `infracost breakdown --format json`.")
    inputs.add_argument("--source-dir", default=".", help="Terraform source to pack alongside the documents.")
    inputs.add_argument(
        "--no-source",
        action="store_true",
        help="Send only the documents. Discovery still looks in --source-dir (or .) for the plan.",
    )

    run = check.add_argument_group("run")
    run.add_argument("--sha", default=None, help="Commit SHA, used to namespace the uploaded archive.")
    run.add_argument(
        "--artifact-tag",
        default="default",
        help=(
            "Namespaces the archive within a commit. Needed only when one workflow evaluates the same "
            "commit more than once -- a plan phase and a state phase, or matrix legs sharing a workflow."
        ),
    )
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
    try:
        opts.api_url, opts.dashboard_url, url_warnings = regions.resolve(
            region_id=opts.region,
            api_url=opts.api_url,
            dashboard_url=opts.dashboard_url,
            env=os.environ,
        )
    except ValueError as e:
        log(f"ERROR: {e}")
        return ExitStatus.ERROR
    for warning in url_warnings:
        log(f"WARNING: {warning}")
    opts.source_dir = None if opts.no_source else opts.source_dir

    missing = [name for name, value in (("--api-key", opts.api_key), ("--org", opts.org)) if not value]
    if missing:
        log(f"ERROR: missing required {' and '.join(missing)}")
        return ExitStatus.ERROR

    if not WORKFLOW_ID_PATTERN.match(opts.workflow_id):
        # Checked before any HTTP call: the value goes straight into every API path, and the
        # platform's own field is a slug, so a `/` yields a malformed URL rather than a clear error.
        suggestion = re.sub(r"[^A-Za-z0-9_-]+", "-", opts.workflow_id).strip("-").lower()[:100]
        log(f"ERROR: --workflow-id '{opts.workflow_id}' is not a valid slug. Try '{suggestion}'.")
        return ExitStatus.ERROR

    opts.input_document = None
    if opts.plan_file:
        if opts.input_path:
            log("ERROR: --plan-file and --input-path cannot be combined; they name the same document")
            return ExitStatus.ERROR
        try:
            opts.input_document = discover.terraform_show_json(
                opts.plan_file, workdir=opts.source_dir, binary=opts.terraform_bin
            )
        except discover.DiscoveryError as e:
            log(f"ERROR: {e}")
            return ExitStatus.ERROR
        log(f"Rendered {opts.plan_file} with `terraform show -json`")
    elif not opts.input_path and not opts.state_path:
        # Nothing was named, so look in the conventional place. This is what lets a caller run with
        # no configuration at all.
        try:
            opts.input_path = discover.discover_input(opts.source_dir)
        except discover.DiscoveryError as e:
            log(f"ERROR: {e}")
            return ExitStatus.ERROR
        log(f"Using {opts.input_path}")

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
    if verdict == "failed" and opts.fail_on_error:
        return ExitStatus.ERROR_POLICY_FAILED
    if verdict == "failed":
        log("Policies failed, but --fail-on-error was not set")
    # A policy asking for approval warns rather than gating -- see report.verdict for why.
    if result.get("counts", {}).get("approval_required"):
        log("Some policies ask for approval; reported as a warning, which does not block")

    return ExitStatus.SUCCESS
