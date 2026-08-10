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
from .client import ARCHIVE_DOCUMENT, ARCHIVE_NAME_TEMPLATE, SGClient, SGError

DEFAULT_WORKFLOW_GROUP = "default"
DEFAULT_TERRAFORM_VERSION = "1.5.7"

# What the CLI understands as an input document. `terraform_state` exists as a distinct kind from
# `json` purely so this side knows to mask it -- tirith itself has no state provider, and the step
# routes it to the json provider.
INPUT_KINDS = ("terraform_plan", "terraform_state", "kubernetes", "json")

# The bundle's name lives in client.ARCHIVE_NAME_TEMPLATE, and the reasoning is worth keeping here
# because it inverted twice while this was built.
#
# It began as `__sg.{sha}-{tag}.tar.gz`. The `__sg.` prefix deliberately kept it OUT of the artifact
# sync, because that prefix is pulled into every run's working directory and pushed back with no
# --delete. Once the sync became the *delivery* mechanism -- the step reads the bundle out of
# $LOCAL_ARTIFACTS_DIR -- being excluded from it was exactly wrong, so the name must match none of the
# sync's exclude patterns (`sg.*`, `*__sg.*`, `*pci_*`, the compliance globs) and must not be
# `tfstate.json`.
#
# The sha stays, though, and it is load-bearing. A name shared by every run of the workflow is a name
# two concurrent runs can overwrite -- and the action derives one workflow id per repository, so two
# open pull requests is the ordinary case, not a corner. One run would then evaluate the other's code
# and report the verdict as its own, silently, on a merge gate. Per commit, that cannot happen.
#
# It is affordable because the name is per *run*, not per workflow: core merges the run's
# TerraformConfig over the workflow's, so each run names its own bundle in its own
# `prePlanWfStepsConfig`. The workflow's stored copy is only a fallback.
#
# The cost is growth -- bundles accumulate in a prefix with no lifecycle rule, no --delete on either
# sync, and no artifact DELETE in api, so every later run downloads all of them. Taken deliberately:
# correctness over transfer cost. `client.delete_artifact` is kept for a retention sweep to use.

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


# The step template that evaluates the policies, and the name its run stage takes.
POLICY_STEP_TEMPLATE = "/stackguardian/tirith-iac-governance:1"
POLICY_STEP_NAME = "evaluate-policies"
POLICY_STEP_TIMEOUT = 1800


def policy_step(step_template_id, bundle_path):
    """
    The pre-plan step entry, naming the bundle this run should evaluate.

    Sent in full on every run rather than relying on the copy stored on the workflow. core merges the
    run's TerraformConfig over the workflow's (`workflowruns/__init__.py:1646`), and that merge is
    shallow -- supplying `prePlanWfStepsConfig` replaces the whole list -- so the entry has to carry
    its template id and timeout too, not just the path.
    """
    return {
        "name": POLICY_STEP_NAME,
        "wfStepTemplateId": step_template_id or POLICY_STEP_TEMPLATE,
        "timeout": POLICY_STEP_TIMEOUT,
        "approval": False,
        # Everything the step needs travels here. It reads nothing from the workflow's terraform
        # configuration.
        "wfStepInputData": {"schemaType": "FORM_JSONSCHEMA", "data": {"bundlePath": bundle_path}},
    }


def terraform_config(terraform_version, step_template_id):
    """
    The workflow's stored configuration, carrying the policy step as a PRE-PLAN step.

    This is the whole mechanism, and it uses only primitives the platform already had. core splices
    `prePlanWfStepsConfig` ahead of `generate-terraform-plan`, and a step exiting 12 tells the run
    controller to complete the run successfully and skip everything after it. So the policy step runs,
    exits 12, and the terraform plan never happens -- without core knowing anything about this feature.

    That is why the run's TerraformAction is `plan`: a dummy value, never acted on, chosen because it
    is the action whose synthesis splices pre-plan steps in.

    `managedTerraformState` stays False -- a policy check writes no state, and it must not take the
    managed-state backend override even on a workflow configured for one.

    Deliberately carries no "input kind". The step routes on which document is present in the
    archive, because a stored kind cannot be trusted: a two-phase pipeline gates the plan and then
    checks the state against the SAME workflow, whose identity derives from the repository and
    workflow name. The workflow is created once, by whichever phase ran first, so the stored kind was
    that phase's and the other phase fed its document to a provider that cannot read it.

    The `bundlePath` stored here is only a fallback. This configuration is written once, at workflow
    creation -- `ensure_workflow` returns 409 for an existing workflow and updates nothing -- so it
    cannot describe any particular run. Every run therefore sends its own `prePlanWfStepsConfig` in the
    run body, which core merges over this one, naming that run's bundle.
    """
    config = {
        "terraformVersion": terraform_version or DEFAULT_TERRAFORM_VERSION,
        "managedTerraformState": False,
        "prePlanWfStepsConfig": [policy_step(step_template_id, ARCHIVE_DOCUMENT)],
    }
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
            source_dir=source_dir,
            plan=plan,
            state=state,
            infracost=infracost,
            document_sources=document_sources,
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
        archive_bytes, manifest = archive.pack(
            source_dir=None, plan=plan, state=state, infracost=infracost
        )
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
    # beside the masked copy.
    #
    # `plan_file` belongs here most of all, and was the omission that made this half a fix:
    # --plan-file converts the BINARY plan in memory precisely so nothing unmasked touches the
    # disk, but the binary plan itself is already on disk, and it embeds the prior state -- every
    # attribute of every existing resource. The `tfplan` name patterns in DEFAULT_EXCLUDES only
    # cover the spellings the README happens to use; `terraform plan -out=plan.out` is at least as
    # common, and that file is the one thing here worth protecting most.
    archive_bytes, manifest, source_skipped = pack_documents(
        opts.source_dir,
        plan,
        state,
        infracost,
        document_sources=(opts.input_path, opts.state_path, opts.infracost_path, getattr(opts, "plan_file", None)),
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
            terraform_config(opts.terraform_version, opts.step_template_id),
            vcs_config=SGClient.vcs_config(getattr(opts, "repo_url", None), getattr(opts, "repo_ref", None)),
        )

        # A flat, fixed name at the artifact root, overwritten every run. The step finds it there
        # because the run controller syncs that directory down before any step executes -- which is
        # what removes the need for any run-creation field, and therefore for any api change at all.
        bundle_name = ARCHIVE_NAME_TEMPLATE.format(
            sha=opts.sha[:7] if opts.sha else "latest", tag=opts.artifact_tag
        )
        key = client.upload_file(
            opts.workflow_group,
            opts.workflow_id,
            bundle_name,
            None,
            archive_bytes,
        )
        log(f"Uploaded the project archive: {key}")

        if state is not None:
            upload_state_document(client, opts, state)

        # The run names its own bundle. core merges this over the workflow's stored TerraformConfig,
        # which is what makes the name per-run even though the workflow's copy was written once and
        # never updated -- and therefore what lets the name carry the commit instead of being shared
        # by every run of the workflow.
        run_id, _data = client.create_run(
            opts.workflow_group,
            opts.workflow_id,
            opts.trigger_details,
            pre_plan_steps=[policy_step(opts.step_template_id, bundle_name)],
        )
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
    # One object per workflow, replaced on every run, so retention costs a bounded amount rather than
    # growing per commit. It does land in the artifact prefix that is synced into every later run of
    # the workflow -- unavoidable, because that sync is how the step receives it -- but the step
    # deletes it from the volume after unpacking, so it does not travel onward from there.
    #
    # `client.delete_artifact` is kept for a retention sweep to use later. Note it currently points at
    # a view that serves only GET and POST.
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
            # Published so a consumer can tell "nothing failed" from "we could not read part of
            # it". Without it an errored run reported failed: 0, which the action copies straight
            # to its `failed` output.
            "unknown": counts.get(report.UNKNOWN, 0),
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
