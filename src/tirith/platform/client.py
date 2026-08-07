"""
StackGuardian API client.

stdlib only -- urllib rather than requests -- so this adds no dependency to a package that has
three, and a CI runner needs nothing installed beyond tirith itself.

  POST /orgs/<org>/wfgrps/                                       create the workflow group
  POST /orgs/<org>/wfgrps/<grp>/wfs/                              create the workflow
  GET  /orgs/<org>/wfgrps/<grp>/wfs/<wf>/file_upload_url/          presigned PUT (5 min) + key
  POST /orgs/<org>/wfgrps/<grp>/wfs/<wf>/wfruns/                  create the run
  GET  /orgs/<org>/wfgrps/<grp>/wfs/<wf>/wfruns/<run>/            poll
  GET  /orgs/<org>/wfgrps/<grp>/wfs/<wf>/artifacts/<path>/        fetch the results artifact
  GET  .../wfruns/<run>/wfrunfacts/<facts>/                       fallback -> PolicyEvalResults
"""

import gzip
import json
import time
import urllib.error
import urllib.parse
import urllib.request

from . import regions

# Signed into the upload URL by the platform, so the PUT must send the same value.
ARCHIVE_CONTENT_TYPE = "application/gzip"

# The run-creation field naming the uploaded project archive, and the RuntimeParameters key core
# stores it under. The run controller keys off the stored one; a mismatch anywhere along that chain
# means the archive is silently ignored and the run falls back to a VCS checkout, which for a
# workflow created by this client is no checkout at all. Hence the read-back in create_run.
CODE_ZIP_FIELD = "CodeZipWfArtifactPath"
CODE_ZIP_RUNTIME_KEY = "codeZipWfArtifactPath"

# Terminal run states. QUEUED/PENDING/RUNNING are transient; a run can sit in QUEUED for a long
# while behind the per-workflow concurrency gate, which is why the caller logs each poll.
#
# APPROVAL_REQUIRED is terminal *for polling purposes*: it is a resting state, reached when a
# policy's onFail is APPROVAL_REQUIRED, and nothing further happens without a human. Treating it as
# transient would spin until the timeout and then report a tool failure for what is actually a
# completed evaluation. sg-cli treats it the same way.
TERMINAL_STATUSES = ("COMPLETED", "ERRORED", "CANCELLED", "APPROVAL_REQUIRED")

RETRYABLE_STATUS = (408, 429, 500, 502, 503, 504)


class SGError(Exception):
    """An API call failed in a way the caller cannot recover from."""


def _extract_signed_url(payload):
    """
    Pull the presigned URL out of an upload-url response.

    The shape varies by endpoint and deployment: the tfstate/file upload endpoints return the URL
    as a bare string in `msg`, while the newer template-artifact endpoints nest it under
    `data.signedUrl`. Accept either rather than depending on one.
    """
    if not isinstance(payload, dict):
        return None

    for container_key in ("data", "msg"):
        container = payload.get(container_key)
        if isinstance(container, str) and container.startswith("http"):
            return container
        if isinstance(container, dict):
            for url_key in ("signedUrl", "signed_url", "url"):
                candidate = container.get(url_key)
                if isinstance(candidate, str) and candidate.startswith("http"):
                    return candidate
    return None


class SGClient:
    def __init__(self, api_url, org, api_key, user_agent="tirith-action", timeout=60):
        # Accepts a base with or without /api/v1, so a SG_BASE_URL exported for sg-cli works here.
        self.api_url = regions.normalize_api_url(api_url) or regions.normalize_api_url(
            regions.by_id(regions.DEFAULT_REGION_ID).api_base
        )
        self.org = org
        self.api_key = api_key
        self.user_agent = user_agent
        self.timeout = timeout

    # -- plumbing ------------------------------------------------------------------------------

    def _request(self, method, path, body=None, retries=4):
        url = f"{self.api_url}/orgs/{urllib.parse.quote(self.org)}{path}"
        data = json.dumps(body).encode() if body is not None else None

        last_error = None
        for attempt in range(retries + 1):
            request = urllib.request.Request(url, data=data, method=method)
            # SG's documented scheme. Must be an sgo_ (org) token: sgu_ tokens are non-functional
            # for SSO-group-only users and inherit only direct permissions for hybrid SSO users,
            # which surfaces as a confusing 403.
            request.add_header("Authorization", f"apikey {self.api_key}")
            request.add_header("Content-Type", "application/json")
            request.add_header("X-SG-Client", self.user_agent)

            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    raw = response.read()
                    return response.status, (json.loads(raw) if raw else {})
            except urllib.error.HTTPError as e:
                raw = e.read()
                try:
                    payload = json.loads(raw) if raw else {}
                except json.JSONDecodeError:
                    payload = {"msg": raw.decode("utf-8", "replace")[:500]}

                if e.code in RETRYABLE_STATUS and attempt < retries:
                    last_error = f"HTTP {e.code}: {payload.get('msg', '')}"
                    time.sleep(min(2**attempt, 8))
                    continue
                return e.code, payload
            except (urllib.error.URLError, TimeoutError) as e:
                # Never treat a network failure as a pass -- the caller maps this to a red check.
                last_error = str(e)
                if attempt < retries:
                    time.sleep(min(2**attempt, 8))
                    continue
                raise SGError(f"Could not reach StackGuardian at {self.api_url}: {last_error}")

        raise SGError(f"StackGuardian request failed after {retries + 1} attempts: {last_error}")

    # -- resources -----------------------------------------------------------------------------

    def ensure_workflow_group(self, name):
        """
        Create the workflow group if absent.

        Needed because `createIfNotExists` on run creation auto-creates the *workflow*, not the
        group -- core's own error for a missing group reads "Workflow Group does not exist and
        cannot be created". A 409 means someone else already made it, which is success here.
        """
        status, payload = self._request(
            "POST",
            "/wfgrps/",
            {"ResourceName": name, "Description": "Created by tirith", "Tags": ["sg-created"]},
        )
        if status in (200, 201, 409):
            return status
        raise SGError(f"Could not create workflow group '{name}' (HTTP {status}): {payload.get('msg')}")

    @staticmethod
    def vcs_config(repo_url, repo_ref=None):
        """
        Build the workflow's VCSConfig from a repo URL, recording where the code came from.

        `GIT_OTHER` -- singular, the wire value behind the UI's "Git Others" -- is the
        connector-less provider. With `isPrivate: false` it needs no auth at all, and it skips the
        GitHub repo-id extraction that rejects anything it cannot parse as an owner/name pair.

        This is metadata only. Nothing clones it: core pops `iacVCSConfig` from the run's
        RuntimeParameters whenever an archive is named, and the runner takes the archive
        branch of its if/elif regardless. It exists so the workflow shows a repo link instead of a
        "configure" prompt.
        """
        if not repo_url:
            return None
        config = {"isPrivate": False, "repo": repo_url}
        if repo_ref:
            config["ref"] = repo_ref
        return {
            "iacVCSConfig": {
                "useMarketplaceTemplate": False,
                "customSource": {"sourceConfigDestKind": "GIT_OTHER", "config": config},
            }
        }

    def ensure_workflow(self, wfgrp, workflow_id, description, terraform_config, vcs_config=None):
        """
        Create the workflow if absent, keyed on `Id`.

        `Id` is the stable slug identity and what goes in the URL; `ResourceName` is a display name
        and is not unique. Both are set to the same string so there is one name to reason about.
        Note `Id` is a DRF SlugField, so it cannot contain dots.

        The workflow is `TERRAFORM`, not `CUSTOM`. For a terraform workflow core synthesises the
        steps from the stored TerraformConfig plus the per-run TerraformAction and *ignores* any
        WfStepsConfig in the request -- so the step configuration has to live here, once, rather
        than being sent on every run. It also means the run renders as a real terraform run in the
        dashboard rather than as opaque custom steps.

        `vcs_config` is set on creation only -- a 409 means the workflow already exists and nothing
        is updated, so a workflow created before this existed keeps its blank repo field.
        """
        body = {
            "Id": workflow_id,
            "ResourceName": workflow_id,
            "Description": description,
            "Tags": ["sg-created", "tirith"],
            "WfType": "TERRAFORM",
            "TerraformConfig": terraform_config,
        }
        if vcs_config:
            body["VCSConfig"] = vcs_config

        status, payload = self._request("POST", f"/wfgrps/{urllib.parse.quote(wfgrp)}/wfs/", body)
        if status in (200, 201, 409):
            return status
        raise SGError(f"Could not create workflow '{workflow_id}' (HTTP {status}): {payload.get('msg')}")

    def manages_terraform_state(self, wfgrp, workflow_id):
        """
        Whether the workflow keeps its terraform state on the platform.

        Consulted before writing `artifacts/tfstate.json`, because for a managed-state workflow that
        object *is* the live state: the step's backend writes it, state locking keys on the literal
        name, and the state-backends view lists it. Overwriting it with a masked document would be
        data loss, so this is a hard gate rather than a warning.

        Unreadable answers as True -- the safe direction. Not being able to tell whether an object is
        live state is not a reason to overwrite it.
        """
        status, payload = self._request("GET", f"/wfgrps/{urllib.parse.quote(wfgrp)}/wfs/{workflow_id}/")
        if status != 200:
            return True
        body = payload.get("msg") or payload.get("data") or {}
        if not isinstance(body, dict) or "TerraformConfig" not in body:
            # A 200 that carries no TerraformConfig is still an answer we cannot read. Absent is not
            # the same as false.
            return True
        return bool((body.get("TerraformConfig") or {}).get("managedTerraformState"))

    # `content` rather than `payload`: the response variable below is already called payload, and
    # shadowing it sent the JSON response body to S3 in place of the file.
    def upload_file(self, wfgrp, workflow_id, filename, folder, content, content_type=ARCHIVE_CONTENT_TYPE):
        r"""
        Upload one object into the workflow's artifact prefix via a presigned PUT, returning its key.

        For the project archive the key is what the caller passes back as CodeZipWfArtifactPath when
        creating the run. It comes from the response rather than being rebuilt here: the layout is
        runner-aware (a private runner's own S3 bucket or Azure container rather than the shared
        bucket), so a client-side guess would be wrong for exactly the customers who are hardest to
        debug.

        `folder` is optional and must be a flat token -- the endpoint rejects `/`, `\\` and `..` to
        prevent path traversal. Omitting it puts the object at the artifacts root, which is what both
        callers want: the archive because a nested key cannot be deleted correctly, and the state
        document because `artifacts/tfstate.json` is the canonical location the platform reads.
        """
        params = {"filename": filename, "contentType": content_type}
        if folder:
            # Only when set. urlencode stringifies None to the literal "None", and the endpoint
            # treats any non-empty value as a subfolder -- so passing it unconditionally produced a
            # real `None/` directory in S3, and the archive then sat at a nested key that the
            # post-run delete could not address.
            params["folder"] = folder
        query = urllib.parse.urlencode(params)
        status, payload = self._request(
            "GET", f"/wfgrps/{urllib.parse.quote(wfgrp)}/wfs/{workflow_id}/file_upload_url/?{query}"
        )
        if status != 200:
            raise SGError(f"Could not get an upload URL for {filename} (HTTP {status}): {payload.get('msg')}")

        key = (payload.get("data") or {}).get("key")
        if not key:
            raise SGError(
                f"The upload response for {filename} carried no storage key (data.key). The "
                f"platform may predate the key being returned from file_upload_url. "
                f"Response: {payload}"
            )
        signed_url = _extract_signed_url(payload)
        if not signed_url:
            raise SGError(f"No signed URL in the upload response for {filename}: {payload}")

        # Must match the content type the URL was signed with, or S3 rejects it as a signature
        # mismatch.
        put = urllib.request.Request(signed_url, data=content, method="PUT")
        put.add_header("Content-Type", content_type)
        try:
            with urllib.request.urlopen(put, timeout=self.timeout) as response:
                if response.status not in (200, 204):
                    raise SGError(f"Upload of {filename} returned HTTP {response.status}")
        except urllib.error.HTTPError as e:
            # The signed URL is valid for 5 minutes; an expiry shows up here as a 403.
            raise SGError(f"Upload of {filename} failed (HTTP {e.code}): {e.read()[:300]!r}")
        except (urllib.error.URLError, TimeoutError) as e:
            raise SGError(f"Upload of {filename} failed: {e}")

        return key

    def create_run(self, wfgrp, workflow_id, project_zip_key, trigger_details, action="tirith-iac-governance"):
        """
        Create one workflow run. Every invocation makes a new run.

        Deliberately carries no WfStepsConfig: core ignores it for TERRAFORM workflows and
        synthesises the steps from the workflow's TerraformConfig and this TerraformAction. The
        only per-run state is the archive key and where the run came from.

        The archive travels as `CodeZipWfArtifactPath`, which core stores under RuntimeParameters.
        `terraformProjectZip` expresses the same thing but belongs to the CLI-driven workflow
        feature; a separate key keeps the two distinguishable, so a rule that ties an archive to one
        action can be written without touching the other's path.

        A context tag was the obvious-looking alternative and is the wrong tool: run context tags are
        indexed into global search, so an internal storage key would surface in customers' tag
        typeaheads and could be enumerated by filtering on it.
        """
        body = {
            "TerraformAction": {"action": action},
            CODE_ZIP_FIELD: project_zip_key,
            "TriggerDetails": trigger_details,
        }
        status, payload = self._request("POST", f"/wfgrps/{urllib.parse.quote(wfgrp)}/wfs/{workflow_id}/wfruns/", body)
        if status not in (200, 201):
            raise SGError(f"Could not create the workflow run (HTTP {status}): {payload.get('msg')}")

        data = payload.get("data") or {}
        run_name = data.get("ResourceName")
        if not run_name:
            raise SGError(f"No ResourceName in the run-creation response: {payload}")

        # A platform that predates the field drops it during request validation and the run then
        # falls back to a VCS checkout -- the wrong code, evaluated without complaint. Assert it
        # back rather than let that pass as a result. Only when the response says: an older
        # response shape that omits RuntimeParameters is not evidence either way.
        runtime_parameters = data.get("RuntimeParameters")
        if isinstance(runtime_parameters, dict) and not runtime_parameters.get(CODE_ZIP_RUNTIME_KEY):
            raise SGError(
                f"The platform dropped the code bundle reference: run {run_name} came back without "
                f"RuntimeParameters.{CODE_ZIP_RUNTIME_KEY}. It would evaluate a VCS checkout instead "
                f"of the uploaded code. The platform may predate {CODE_ZIP_FIELD}."
            )

        return run_name, data

    def get_run(self, wfgrp, workflow_id, run_id):
        status, payload = self._request(
            "GET", f"/wfgrps/{urllib.parse.quote(wfgrp)}/wfs/{workflow_id}/wfruns/{run_id}/"
        )
        if status != 200:
            raise SGError(f"Could not read run {run_id} (HTTP {status}): {payload.get('msg')}")
        # This endpoint returns the run object under "msg" rather than "data".
        return payload.get("msg") or payload.get("data") or {}

    def wait_for_run(self, wfgrp, workflow_id, run_id, timeout=1800, interval=10, on_poll=None):
        """
        Poll until the run reaches a terminal state.

        A timeout is a failure, never a pass: the caller maps it to a red check. `on_poll` exists
        so the caller can log each status -- a run stuck in QUEUED behind another run on the same
        workflow looks identical to a hung run otherwise.
        """
        deadline = time.time() + timeout
        last_status = None

        while time.time() < deadline:
            run = self.get_run(wfgrp, workflow_id, run_id)
            status = run.get("LatestStatus")
            if status != last_status and on_poll:
                on_poll(status)
            last_status = status

            if status in TERMINAL_STATUSES:
                return status, run
            time.sleep(interval)

        raise SGError(
            f"Run {run_id} did not finish within {timeout}s (last status: {last_status}). "
            f"Runs on one workflow serialize, so it may be queued behind another run."
        )

    def get_results_artifact(self, wfgrp, workflow_id, artifact_path):
        """
        Read the results artifact the tirith step used to publish next to the inputs.

        Kept only so a newer CLI still reads results from an older step image. Current step images
        do not write this file: it carried exactly the PolicyEvalResults that the run facts already
        hold, and it existed only because the facts endpoint used to answer "does not exist" for
        every run. That was a key mismatch in the run controller, not a missing record.

        Returns None -- not {} -- when absent, so the caller can tell "no such artifact, go ask the
        facts endpoint" from "the artifact exists and no policies matched".
        """
        status, payload = self._request(
            "GET",
            f"/wfgrps/{urllib.parse.quote(wfgrp)}/wfs/{workflow_id}/artifacts/{artifact_path}/",
        )
        if status != 200:
            return None

        # This endpoint returns the artifact body directly rather than an envelope.
        if isinstance(payload, dict) and "PolicyEvalResults" in payload:
            return payload.get("PolicyEvalResults") or {}
        return None

    def get_run_facts(self, wfgrp, workflow_id, run_id):
        """
        Fetch the whole run-facts document. Returns {} when it cannot be read.

        One call, because the document carries everything the caller reports on --
        PolicyEvalResults, the cost breakdown, the plan -- and it embeds the full plan, so it is
        large enough that fetching it twice is worth avoiding.

        The endpoint hands back a presigned GET rather than the payload inline, for the same reason.
        """
        status, payload = self._request(
            "GET",
            f"/wfgrps/{urllib.parse.quote(wfgrp)}/wfs/{workflow_id}/wfruns/{run_id}/wfrunfacts/default/",
        )
        if status != 200:
            return {}

        body = payload.get("msg") or payload.get("data") or {}
        if isinstance(body, dict) and body.get("PolicyEvalResults"):
            return body

        # Via the shared helper: this endpoint returns `signed_url`, not `signedUrl`. Reading only
        # the camelCase spelling meant this always fell through to {} -- which went unnoticed for as
        # long as the results artifact was covering for it.
        signed_url = _extract_signed_url(payload)
        if not signed_url:
            return {}

        try:
            with urllib.request.urlopen(signed_url, timeout=self.timeout) as response:
                raw = response.read()
            if response.info().get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            return json.loads(raw) or {}
        except Exception:
            return {}

    def get_policy_results(self, wfgrp, workflow_id, run_id):
        """Read PolicyEvalResults from the run facts. This is the primary source of the verdict."""
        return self.get_run_facts(wfgrp, workflow_id, run_id).get("PolicyEvalResults") or {}

    def delete_artifact(self, wfgrp, workflow_id, artifact_name):
        """
        Delete one artifact. Best-effort: returns True on success, False otherwise.

        `artifact_name` must be a single path segment. A nested name is swallowed by the greedy
        <path:wfGrp> converter in the authorizer and matches `DELETE .../wfgrps/<wfGrp>/` -- the
        workflow-group delete -- so it would be checked against entirely the wrong permission.
        """
        status, _payload = self._request(
            "DELETE",
            f"/wfgrps/{urllib.parse.quote(wfgrp)}/wfs/{workflow_id}/artifacts/{artifact_name}/",
        )
        return status in (200, 204, 404)
