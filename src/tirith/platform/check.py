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

# Two properties of this name are load-bearing, and neither is decoration.
#
# The `__sg.` prefix keeps the archive out of the per-run artifact sync. The workflow's artifact
# prefix is pulled into every run's working directory and pushed back with no --delete, so an
# unexcluded name is downloaded by every later run of the workflow, forever. `sg.` alone is not
# enough -- the awscli patterns match the key relative to the sync source, and only the `__sg.`
# spelling is excluded in both runner modes. It also hides the input archive from the dashboard's
# artifact listing.
#
# Flat, with the commit in the *filename* rather than a folder, because the archive is deleted once
# the run finishes and a nested name cannot be deleted correctly: the authorizer's greedy
# <path:wfGrp> converter swallows it, so `DELETE .../artifacts/<sha7>/<name>/` matches
# `DELETE .../wfgrps/<wfGrp>/` -- the workflow-group delete -- and is checked against the wrong
# permission entirely. Keeping the sha and tag in the name preserves uniqueness, so two pull
# requests uploading concurrently still cannot overwrite each other's archive before their runs
# start.
ARCHIVE_NAME_TEMPLATE = "__sg.{sha}-{tag}.tar.gz"

# Deliberately NOT `__sg.`-prefixed, unlike the archive. This one is meant to be seen: it is the name
# the platform already treats as a workflow's state document, so it lands in the State and artifacts
# views rather than being hidden from them. The name is shared with the copy inside the archive
# (`archive.STATE_DOCUMENT`).
STATE_DOCUMENT_NAME = "tfstate.json"
STATE_CONTENT_TYPE = "application/json"


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


def prepare_documents(input_path, input_kind, state_path, infracost_path, input_document=None):
    """
    Read and mask everything that will go into the archive.

    Returns (plan, state, infracost, redaction_count). The returned objects are the *masked* ones;
    nothing downstream should ever touch the originals again.

    `input_document` is an already-parsed document, used by --plan-file so `terraform show -json`
    output goes straight from the pipe into the masker without an unmasked plan ever being written
    to disk.
    """
    plan = None
    state = None
    redactions = 0

    if input_document is not None or input_path:
        document = input_document if input_document is not None else read_json(input_path, "input document")
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


def pack_documents(source_dir, plan, state, infracost, document_sources=()):
    """
    Build the archive, dropping the source tree rather than failing if it is too large.

    Returns (bytes, manifest, source_skipped_reason) where the reason is None on the normal path.

    The source is packed by default, so an exclusion that does not fire -- a committed vendor
    directory, a build output tree -- would otherwise turn a working policy check into a failed run.
    That trade is the wrong way round: the verdict is what gates the merge, and the source is there
    for the autofix system's benefit. So an oversized archive degrades to documents-only and says so,
    loudly, rather than taking the gate down with it.

    Only when a source tree was actually requested. If we are already documents-only and still over
    the limit, the *documents* are too big and there is nothing left to drop, so that stays fatal.
    """
    try:
        archive_bytes, manifest = archive.pack(
            source_dir=source_dir, plan=plan, state=state, infracost=infracost, document_sources=document_sources
        )
        return archive_bytes, manifest, None
    except archive.ArchiveError as e:
        if not source_dir:
            raise

        reason = str(e)
        log(
            f"WARNING: {reason} Uploading the masked documents only, without the source. The policy "
            f"check still runs, but the archive carries no code -- so anything reading it to generate "
            f"fixes has nothing to work from. Point --source-dir at your terraform directory, or add "
            f"the large paths to .gitignore."
        )
        archive_bytes, manifest = archive.pack(source_dir=None, plan=plan, state=state, infracost=infracost)
        return archive_bytes, manifest, reason


def upload_state_document(client, opts, state):
    """
    Also publish the masked state as the workflow's `artifacts/tfstate.json`.

    That name is canonical rather than decorative: the managed-state backend writes it, state locking
    keys on the literal basename, and the state-backends listing special-cases it. Putting the state
    there is what makes it visible and downloadable in the platform's own State and artifacts views,
    instead of being reachable only by unpacking the run's archive.

    It goes *in addition to* the copy inside the archive -- the step reads that one to publish
    `TfStateCleaned`, and the two must not diverge.

    Best-effort: the check's verdict does not depend on it, so a failure warns rather than failing a
    run whose policies evaluated perfectly well.
    """
    if client.manages_terraform_state(opts.workflow_group, opts.workflow_id):
        log(
            "WARNING: not writing tfstate.json -- this workflow manages its own terraform state, and "
            "that object is the live state. Overwriting it with a masked document would be data loss. "
            "The state is still evaluated, and still in the run's archive."
        )
        return

    try:
        key = client.upload_file(
            opts.workflow_group,
            opts.workflow_id,
            STATE_DOCUMENT_NAME,
            None,
            json.dumps(state).encode("utf-8"),
            content_type=STATE_CONTENT_TYPE,
        )
    except SGError as e:
        log(f"WARNING: could not publish {STATE_DOCUMENT_NAME}: {e}")
        return

    log(
        f"Published the state document: {key} -- masked, so it reflects what was evaluated and "
        f"cannot be used to run terraform."
    )


def run_check(opts):
    """
    Execute the check. Returns the result document.

    Raises CheckError for anything that leaves the verdict unknown -- the caller maps that to a
    non-zero exit regardless of --fail-on-error, because a run that produced no verdict must never
    look like a pass.
    """
    client = SGClient(opts.api_url, opts.org, opts.api_key, timeout=60)

    plan, state, infracost, redactions = prepare_documents(
        opts.input_path,
        opts.input_kind,
        opts.state_path,
        opts.infracost_path,
        input_document=getattr(opts, "input_document", None),
    )
    if redactions:
        log(f"Masked {redactions} sensitive value(s) before upload")

    # Every path a document was read from, so the source walk cannot ship the unmasked original
    # beside the masked copy. --plan-file supplies the document in memory and no path, which is
    # exactly the case that needs no exclusion.
    archive_bytes, manifest, source_skipped = pack_documents(
        opts.source_dir,
        plan,
        state,
        infracost,
        document_sources=(opts.input_path, opts.state_path, opts.infracost_path),
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
            vcs_config=SGClient.vcs_config(getattr(opts, "repo_url", None), getattr(opts, "repo_ref", None)),
        )

        archive_name = ARCHIVE_NAME_TEMPLATE.format(sha=opts.sha[:7] if opts.sha else "latest", tag=opts.artifact_tag)
        key = client.upload_file(
            opts.workflow_group,
            opts.workflow_id,
            archive_name,
            None,
            archive_bytes,
        )
        log(f"Uploaded the project archive: {key}")

        if state is not None:
            upload_state_document(client, opts, state)

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

    # The run facts are the source of truth -- they are what the dashboard renders. Fetched once:
    # the document carries the verdict and the cost estimate, and it embeds the whole plan, so it
    # is large enough that fetching it twice is worth avoiding.
    # A read failure is held rather than raised straight away: an older step image publishes its
    # verdict as an artifact instead, and that fallback below is still worth trying. What must not
    # happen is a failed read falling through to an empty result set, which renders as "no policies
    # in scope" -- a clean-looking exit for a run whose policies may well have failed.
    facts_error = None
    try:
        facts = client.get_run_facts(opts.workflow_group, opts.workflow_id, run_id)
    except SGError as e:
        facts = {}
        facts_error = e

    policy_results = facts.get("PolicyEvalResults") or {}
    # PreApply is what the step writes for a check run; the bare key is the fallback for an older
    # step image that only set that one.
    cost_breakdown = facts.get("InfracostBreakdownPreApply") or facts.get("InfracostBreakdown")

    # The results artifact is only consulted when the facts come back empty, which means an older
    # step image that still writes it.
    legacy = None
    if not policy_results:
        legacy = client.get_results_artifact(opts.workflow_group, opts.workflow_id, f"{run_id}/tirith-results.json")
        if legacy is not None:
            policy_results = legacy

    # Only when NOTHING answered. `legacy is not None` means the artifact was read and was
    # legitimately empty -- an older step image with no policies in scope -- which is a real
    # no-policies result, not a failed read.
    if facts_error is not None and legacy is None:
        raise CheckError(f"The run completed but its results could not be read: {facts_error} (run: {run_url})")

    # The archive is deliberately retained. It is the source that produced these findings, and the
    # autofix system reads it to generate fixes -- so deleting it here would remove the only copy of
    # what was actually evaluated.
    #
    # Retaining it is safe for the *runs*: the `__sg.` prefix keeps it out of the per-run artifact
    # sync, so it never lands in a later run's working directory, which was the problem worth
    # solving. It is not free, though: nothing prunes this prefix -- no lifecycle rule, and neither
    # sync passes --delete -- so this is one object per commit and tag, kept indefinitely.
    #
    # `client.delete_artifact` is kept for a retention sweep to use later.
    log(f"Retained the project archive for autofix: {key}")

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
        # Surfaced for a caller aggregating several units into one comment of their own.
        "monthly_cost": (cost_breakdown or {}).get("totalMonthlyCost"),
        # Where the evaluated source lives. The autofix system reads this to fetch what produced
        # the findings; it is also recorded on the run itself as SGCustomWorkflowRunFacts, so a
        # consumer holding only a run id can find it without seeing this document.
        "archive_key": key,
        # Whether that archive actually contains the source. Normally true, and false when the tree
        # was too large and got dropped so the check could still run. A consumer must not assume:
        # "no code in the bundle" and "no code was wanted" need to be distinguishable.
        "source_packed": bool(opts.source_dir) and source_skipped is None,
        "source_skipped_reason": source_skipped,
    }

    write_output_json(opts.output_json, result)

    if opts.output_markdown:
        body = report.render_markdown(
            policy_results,
            status,
            run_url,
            marker=opts.comment_marker,
            limit=opts.markdown_limit,
            cost_breakdown=cost_breakdown,
            commit=opts.sha,
        )
        try:
            with open(opts.output_markdown, "w") as f:
                f.write(body)
        except OSError as e:
            log(f"WARNING: could not write {opts.output_markdown}: {e}")

    log(result["headline"])
    return result
