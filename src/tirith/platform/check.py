"""
Orchestration for `tirith platform check`.

    read -> mask -> pack -> ensure workflow -> upload archive -> create run -> poll -> fetch -> report

The masking is the part that matters most and it happens *here*, on the caller's machine, before
anything leaves it. Masking server-side would be theatre: once the bytes arrive the exposure has
already happened.
"""

import json
import os
import sys

from . import archive, redact, report
from .client import SGClient, SGError

DEFAULT_WORKFLOW_GROUP = "default"
DEFAULT_TERRAFORM_VERSION = "1.5.7"

# What the CLI understands as an input document. `terraform_state` exists as a distinct kind from
# `json` purely so this side knows to mask it -- tirith itself has no state provider, and the step
# routes it to the json provider.
INPUT_KINDS = ("terraform_plan", "terraform_state", "kubernetes", "json")


class CheckError(Exception):
    """The check could not be completed. Always fails closed."""


def log(message):
    """Progress goes to stderr so stdout stays clean for machine-readable output."""
    print(message, file=sys.stderr, flush=True)


def read_json(path, label):
    if not os.path.exists(path):
        raise CheckError(f"{label} not found: {path}")
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise CheckError(f"{label} is not valid JSON ({path}): {e}")
    except OSError as e:
        raise CheckError(f"Could not read {label} ({path}): {e}")


def prepare_documents(input_path, input_kind, state_path, infracost_path):
    """
    Read and mask everything that will go into the archive.

    Returns (plan, state, infracost, redaction_count). The returned objects are the *masked* ones;
    nothing downstream should ever touch the originals again.
    """
    plan = None
    state = None
    redactions = 0

    if input_path:
        document = read_json(input_path, "input document")
        if input_kind == "terraform_plan":
            plan = redact.redact_plan(document)
            redactions += redact.count_redactions(plan)
        elif input_kind == "terraform_state":
            state = redact.redact_state(document)
            redactions += redact.count_redactions(state)
        else:
            # kubernetes / json: no marker structure to drive masking, so it goes as-is. Warn if it
            # looks like state, because that is the mistake that would ship every attribute in
            # plaintext.
            if isinstance(document, dict) and {"version", "lineage", "resources"} <= set(document):
                log(
                    "WARNING: this document looks like terraform state but --input-kind is "
                    f"'{input_kind}', so it will NOT be masked. Use --input-kind terraform_state."
                )
            plan = document

    if state_path:
        state_document = read_json(state_path, "state document")
        masked_state = redact.redact_state(state_document)
        redactions += redact.count_redactions(masked_state)
        if state is None:
            state = masked_state
        else:
            log("Both --input-path and --state-path are state documents; using --input-path")

    infracost = read_json(infracost_path, "cost breakdown") if infracost_path else None

    return plan, state, infracost, redactions


def terraform_config(terraform_version, policy_input_kind, step_template_id):
    """
    The workflow's stored configuration.

    core synthesises the run's steps from this plus the per-run TerraformAction, so anything the
    step needs that does not vary per run belongs here.
    """
    config = {
        "terraformVersion": terraform_version or DEFAULT_TERRAFORM_VERSION,
        "managedTerraformState": False,
        "policyInputKind": policy_input_kind,
    }
    if step_template_id:
        config["wfStepTemplateRevisionId"] = step_template_id
    return config


def write_output_json(path, payload):
    if not path:
        return
    try:
        with open(path, "w") as f:
            json.dump(payload, f, indent=2)
    except OSError as e:
        log(f"WARNING: could not write {path}: {e}")


def run_check(opts):
    """
    Execute the check. Returns the result document.

    Raises CheckError for anything that leaves the verdict unknown -- the caller maps that to a
    non-zero exit regardless of --fail-on-error, because a run that produced no verdict must never
    look like a pass.
    """
    client = SGClient(opts.api_url, opts.org, opts.api_key, timeout=60)

    plan, state, infracost, redactions = prepare_documents(
        opts.input_path, opts.input_kind, opts.state_path, opts.infracost_path
    )
    if redactions:
        log(f"Masked {redactions} sensitive value(s) before upload")

    archive_bytes, manifest = archive.pack(
        source_dir=opts.source_dir,
        plan=plan,
        state=state,
        infracost=infracost,
    )
    log(
        f"Packed {manifest['files']} file(s) and {len(manifest['documents'])} document(s) "
        f"into {manifest['bytes'] // 1024} KB"
    )

    try:
        client.ensure_workflow_group(opts.workflow_group)
        client.ensure_workflow(
            opts.workflow_group,
            opts.workflow_id,
            f"Policy checks for {opts.workflow_id}",
            terraform_config(opts.terraform_version, opts.input_kind, opts.step_template_id),
        )

        key = client.upload_archive(
            opts.workflow_group,
            opts.workflow_id,
            f"{opts.artifact_tag}.tar.gz",
            opts.sha[:7] if opts.sha else "latest",
            archive_bytes,
        )
        log(f"Uploaded the project archive: {key}")

        run_id, _data = client.create_run(opts.workflow_group, opts.workflow_id, key, opts.trigger_details)
    except SGError as e:
        raise CheckError(str(e))

    run_url = (
        f"{opts.dashboard_url.rstrip('/')}/orchestrator/orgs/{opts.org}"
        f"/wfgrps/{opts.workflow_group}/wfs/{opts.workflow_id}/wfruns/{run_id}"
    )
    log(f"Run created: {run_url}")

    # Written before polling so a timeout still leaves the run discoverable.
    write_output_json(opts.output_json, {"status": "RUNNING", "wfrun_id": run_id, "wfrun_url": run_url})

    try:
        status, _run = client.wait_for_run(
            opts.workflow_group,
            opts.workflow_id,
            run_id,
            timeout=opts.timeout,
            on_poll=lambda s: log(f"Run status: {s}"),
        )
    except SGError as e:
        raise CheckError(f"{e} (run: {run_url})")

    policy_results = client.get_results_artifact(opts.workflow_group, opts.workflow_id, f"{run_id}/tirith-results.json")
    if policy_results is None:
        policy_results = client.get_policy_results(opts.workflow_group, opts.workflow_id, run_id)

    counts, _findings = report.summarize(policy_results)
    verdict_value = report.verdict(counts, status)

    result = {
        "status": status,
        "verdict": verdict_value,
        "counts": {
            "passed": counts.get(report.PASS, 0),
            "failed": counts.get(report.FAIL, 0),
            "warned": counts.get(report.WARN, 0),
            "approval_required": counts.get(report.APPROVAL_REQUIRED, 0),
            "skipped": counts.get("SKIPPED", 0),
        },
        "headline": report.headline(counts, verdict_value),
        "wfrun_id": run_id,
        "wfrun_url": run_url,
        "policy_results": policy_results or {},
    }

    write_output_json(opts.output_json, result)

    if opts.output_markdown:
        body = report.render_markdown(
            policy_results, status, run_url, marker=opts.comment_marker, limit=opts.markdown_limit
        )
        try:
            with open(opts.output_markdown, "w") as f:
                f.write(body)
        except OSError as e:
            log(f"WARNING: could not write {opts.output_markdown}: {e}")

    log(result["headline"])
    return result
