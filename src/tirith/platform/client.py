"""
StackGuardian API client.

stdlib only -- urllib rather than requests -- so this adds no dependency to a package that has
three, and a CI runner needs nothing installed beyond tirith itself.

  POST /orgs/<org>/wfgrps/                                       create the workflow group
  POST /orgs/<org>/wfgrps/<grp>/wfs/                              create the workflow
  GET  /orgs/<org>/wfgrps/<grp>/wfs/<wf>/configuration_upload_url/  presigned PUT (5 min) + key
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

DEFAULT_API_URL = "https://api.app.stackguardian.io/api/v1"

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
        self.api_url = (api_url or DEFAULT_API_URL).rstrip("/")
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

    def ensure_workflow(self, wfgrp, workflow_id, description, terraform_config):
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
        """
        status, payload = self._request(
            "POST",
            f"/wfgrps/{urllib.parse.quote(wfgrp)}/wfs/",
            {
                "Id": workflow_id,
                "ResourceName": workflow_id,
                "Description": description,
                "Tags": ["sg-created", "tirith"],
                "WfType": "TERRAFORM",
                "TerraformConfig": terraform_config,
            },
        )
        if status in (200, 201, 409):
            return status
        raise SGError(f"Could not create workflow '{workflow_id}' (HTTP {status}): {payload.get('msg')}")

    def upload_archive(self, wfgrp, workflow_id, filename, folder, archive_bytes):
        """
        Upload the project archive via a presigned PUT, returning its storage key.

        The key is what the caller passes back as `terraformProjectZip` when creating the run. It
        comes from the response rather than being rebuilt here: the layout is runner-aware (a
        private runner's own S3 bucket or Azure container rather than the shared bucket), so a
        client-side guess would be wrong for exactly the customers who are hardest to debug.

        `folder` must be a flat token -- the endpoint rejects `/`, `\\` and `..` to prevent path
        traversal.
        """
        query = urllib.parse.urlencode({"filename": filename, "folder": folder})
        status, payload = self._request(
            "GET", f"/wfgrps/{urllib.parse.quote(wfgrp)}/wfs/{workflow_id}/configuration_upload_url/?{query}"
        )
        if status != 200:
            raise SGError(f"Could not get an upload URL for {filename} (HTTP {status}): {payload.get('msg')}")

        msg = payload.get("msg")
        if not isinstance(msg, dict) or not msg.get("key"):
            raise SGError(
                f"The upload response for {filename} carried no storage key. The platform may "
                f"predate the configuration_upload_url endpoint. Response: {payload}"
            )
        signed_url = _extract_signed_url({"msg": msg.get("signedUrl")})
        if not signed_url:
            raise SGError(f"No signed URL in the upload response for {filename}: {payload}")

        # Must match the content type the URL was signed with, or S3 rejects it as a signature
        # mismatch.
        put = urllib.request.Request(signed_url, data=archive_bytes, method="PUT")
        put.add_header("Content-Type", "application/gzip")
        try:
            with urllib.request.urlopen(put, timeout=self.timeout) as response:
                if response.status not in (200, 204):
                    raise SGError(f"Upload of {filename} returned HTTP {response.status}")
        except urllib.error.HTTPError as e:
            # The signed URL is valid for 5 minutes; an expiry shows up here as a 403.
            raise SGError(f"Upload of {filename} failed (HTTP {e.code}): {e.read()[:300]!r}")
        except (urllib.error.URLError, TimeoutError) as e:
            raise SGError(f"Upload of {filename} failed: {e}")

        return msg["key"]

    def create_run(self, wfgrp, workflow_id, project_zip_key, trigger_details, action="policy-only"):
        """
        Create one workflow run. Every invocation makes a new run.

        Deliberately carries no WfStepsConfig: core ignores it for TERRAFORM workflows and
        synthesises the steps from the workflow's TerraformConfig and this TerraformAction. The
        only per-run state is the archive key and where the run came from.
        """
        body = {
            "TerraformAction": {"action": action},
            "terraformProjectZip": project_zip_key,
            "TriggerDetails": trigger_details,
        }
        status, payload = self._request("POST", f"/wfgrps/{urllib.parse.quote(wfgrp)}/wfs/{workflow_id}/wfruns/", body)
        if status not in (200, 201):
            raise SGError(f"Could not create the workflow run (HTTP {status}): {payload.get('msg')}")

        data = payload.get("data") or {}
        run_name = data.get("ResourceName")
        if not run_name:
            raise SGError(f"No ResourceName in the run-creation response: {payload}")
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
        Read the results artifact the tirith step publishes next to the inputs.

        This is the primary source. The run controller no longer creates a WorkflowRunFacts
        record -- it forwards the facts to the report-aggregator lambda and leaves only a pointer
        on the workflow object -- so the wfrunfacts endpoint answers "does not exist" for runs it
        did produce results for. The artifact is written by our own step, so it is a contract we
        control end to end.
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

    def get_policy_results(self, wfgrp, workflow_id, run_id):
        """
        Fetch PolicyEvalResults from the run fact.

        Retained as a fallback for deployments where the run controller still writes the record.
        The endpoint hands back a presigned GET rather than the payload inline, because the facts
        document embeds the whole plan and can be large.
        """
        status, payload = self._request(
            "GET",
            f"/wfgrps/{urllib.parse.quote(wfgrp)}/wfs/{workflow_id}/wfruns/{run_id}/wfrunfacts/default/",
        )
        if status != 200:
            return {}

        body = payload.get("msg") or payload.get("data") or {}
        if isinstance(body, dict) and body.get("PolicyEvalResults"):
            return body["PolicyEvalResults"]

        signed_url = body.get("signedUrl") if isinstance(body, dict) else None
        if not signed_url:
            return {}

        try:
            with urllib.request.urlopen(signed_url, timeout=self.timeout) as response:
                raw = response.read()
            if response.info().get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            return (json.loads(raw) or {}).get("PolicyEvalResults") or {}
        except Exception:
            return {}
