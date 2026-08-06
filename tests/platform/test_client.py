"""
Tests for the StackGuardian client.

The polling contract is the part worth pinning: a run that rests in a state the poller does not
recognise as terminal spins until the timeout and is then reported as a tool failure -- turning a
completed evaluation into what looks like an outage.
"""

import json

import pytest

from tirith.platform import client
from tirith.platform.client import SGClient, SGError, _extract_signed_url

# --- terminal statuses -------------------------------------------------------------------------


def test_approval_required_is_terminal():
    """
    A regression test. APPROVAL_REQUIRED is a resting state -- reached when a policy's onFail is
    APPROVAL_REQUIRED -- and nothing further happens without a human. Treating it as transient
    made the poller spin to its timeout and report a tool failure for a finished evaluation.
    """
    assert "APPROVAL_REQUIRED" in client.TERMINAL_STATUSES


@pytest.mark.parametrize("status", ["COMPLETED", "ERRORED", "CANCELLED", "APPROVAL_REQUIRED"])
def test_terminal_statuses_stop_the_poll(status):
    assert status in client.TERMINAL_STATUSES


@pytest.mark.parametrize("status", ["QUEUED", "PENDING", "RUNNING"])
def test_transient_statuses_keep_polling(status):
    """A run can sit in QUEUED behind the per-workflow concurrency gate for a long while."""
    assert status not in client.TERMINAL_STATUSES


def test_wait_for_run_returns_on_a_terminal_status(monkeypatch):
    sg = SGClient("https://api.example/api/v1", "acme", "sgo_x")
    statuses = iter([{"LatestStatus": "QUEUED"}, {"LatestStatus": "RUNNING"}, {"LatestStatus": "COMPLETED"}])
    monkeypatch.setattr(sg, "get_run", lambda *a, **k: next(statuses))
    monkeypatch.setattr(client.time, "sleep", lambda _s: None)

    status, _run = sg.wait_for_run("default", "wf", "run", timeout=30)

    assert status == "COMPLETED"


def test_wait_for_run_reports_each_status_change(monkeypatch):
    """Without this a run queued behind another looks identical to a hung one."""
    sg = SGClient("https://api.example/api/v1", "acme", "sgo_x")
    statuses = iter([{"LatestStatus": "QUEUED"}, {"LatestStatus": "QUEUED"}, {"LatestStatus": "COMPLETED"}])
    monkeypatch.setattr(sg, "get_run", lambda *a, **k: next(statuses))
    monkeypatch.setattr(client.time, "sleep", lambda _s: None)
    seen = []

    sg.wait_for_run("default", "wf", "run", timeout=30, on_poll=seen.append)

    assert seen == ["QUEUED", "COMPLETED"], "only changes are reported, not every poll"


def test_wait_for_run_timeout_is_an_error_never_a_pass(monkeypatch):
    sg = SGClient("https://api.example/api/v1", "acme", "sgo_x")
    monkeypatch.setattr(sg, "get_run", lambda *a, **k: {"LatestStatus": "RUNNING"})
    monkeypatch.setattr(client.time, "sleep", lambda _s: None)

    with pytest.raises(SGError):
        sg.wait_for_run("default", "wf", "run", timeout=-1)


# --- signed URL extraction ---------------------------------------------------------------------


def test_extract_signed_url_accepts_a_bare_string_in_msg():
    """What tfstate_upload_url actually returns."""
    assert _extract_signed_url({"msg": "https://s3.example/put"}) == "https://s3.example/put"


def test_extract_signed_url_accepts_a_nested_object():
    assert _extract_signed_url({"data": {"signedUrl": "https://s3.example/put"}}) == "https://s3.example/put"


def test_extract_signed_url_returns_none_when_absent():
    assert _extract_signed_url({"msg": "some error text"}) is None


# --- archive upload ----------------------------------------------------------------------------


def test_upload_archive_requires_a_storage_key(monkeypatch):
    """
    The key is what the caller passes back as the codeZipWfArtifactPath tag. A platform that predates it
    being returned answers with the URL alone, and continuing would create a run pointing at nothing.
    """
    sg = SGClient("https://api.example/api/v1", "acme", "sgo_x")
    monkeypatch.setattr(sg, "_request", lambda *a, **k: (200, {"msg": "https://s3.example/put"}))

    with pytest.raises(SGError, match="storage key"):
        sg.upload_file("default", "wf", "a.tar.gz", "abc1234", b"x")


def _upload_response():
    """What file_upload_url returns: the URL as a bare string in msg, the key alongside in data."""
    return (200, {"msg": "https://s3.example/put", "data": {"key": "orgs/acme/wfs/K/artifacts/abc1234/a.tar.gz"}})


def test_upload_archive_returns_the_key_from_the_response(monkeypatch):
    """
    Never rebuilt client-side: the layout depends on ArtifactsUnderKSUID, ResourceKSUID and
    OriginalArtifactPath, so a guess is wrong for exactly the customers hardest to debug.
    """
    sg = SGClient("https://api.example/api/v1", "acme", "sgo_x")
    monkeypatch.setattr(sg, "_request", lambda *a, **k: _upload_response())
    uploaded = {}

    def fake_urlopen(request, timeout=None):
        uploaded["content_type"] = request.get_header("Content-type")
        uploaded["body"] = request.data

        class _R:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        return _R()

    monkeypatch.setattr(client.urllib.request, "urlopen", fake_urlopen)

    key = sg.upload_file("default", "wf", "a.tar.gz", "abc1234", b"tarbytes")

    assert key == "orgs/acme/wfs/K/artifacts/abc1234/a.tar.gz"
    assert uploaded["body"] == b"tarbytes"
    # Must match what the URL was signed with, or S3 rejects it as a signature mismatch.
    assert uploaded["content_type"] == "application/gzip"


def test_upload_archive_uses_the_shared_artifact_endpoint(monkeypatch):
    """
    Not a bespoke endpoint. The archive is unpacked into the same workflow whose artifacts live
    under this prefix, so it uploads through the same route -- and the contentType it asks to be
    signed with has to match the header the PUT sends.
    """
    sg = SGClient("https://api.example/api/v1", "acme", "sgo_x")
    seen = {}

    def fake_request(method, path, *a, **k):
        seen["method"] = method
        seen["path"] = path
        return _upload_response()

    monkeypatch.setattr(sg, "_request", fake_request)
    monkeypatch.setattr(client.urllib.request, "urlopen", _ok_urlopen())

    sg.upload_file("default", "wf", "a.tar.gz", "abc1234", b"tarbytes")

    assert seen["method"] == "GET"
    assert "/file_upload_url/" in seen["path"]
    assert "configuration_upload_url" not in seen["path"]
    assert "contentType=application%2Fgzip" in seen["path"]
    assert "filename=a.tar.gz" in seen["path"]


def _ok_urlopen():
    def fake_urlopen(request, timeout=None):
        class _R:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        return _R()

    return fake_urlopen


# --- run creation ------------------------------------------------------------------------------


def test_create_run_sends_no_step_config(monkeypatch):
    """
    core ignores WfStepsConfig for TERRAFORM workflows and synthesises the steps from the stored
    TerraformConfig plus this TerraformAction. Sending one would be dead weight that reads as if
    it were doing something.
    """
    sg = SGClient("https://api.example/api/v1", "acme", "sgo_x")
    captured = {}

    def fake_request(method, path, body=None, **kwargs):
        captured["body"] = body
        return 200, {"data": {"ResourceName": "wfrun-1"}}

    monkeypatch.setattr(sg, "_request", fake_request)

    run_id, _data = sg.create_run("default", "wf", "orgs/acme/…/a.tar.gz", {"type": "github_action"})

    assert run_id == "wfrun-1"
    assert "WfStepsConfig" not in captured["body"]
    assert captured["body"]["TerraformAction"] == {"action": "tirith-iac-governance"}
    assert captured["body"]["ContextTags"] == {"codeZipWfArtifactPath": "orgs/acme/…/a.tar.gz"}


def test_ensure_workflow_creates_a_terraform_workflow(monkeypatch):
    """
    TERRAFORM rather than CUSTOM: it is what makes core synthesise the steps from TerraformConfig,
    and what makes the run render as a real terraform run in the dashboard.
    """
    sg = SGClient("https://api.example/api/v1", "acme", "sgo_x")
    captured = {}

    def fake_request(method, path, body=None, **kwargs):
        captured["body"] = body
        return 201, {}

    monkeypatch.setattr(sg, "_request", fake_request)

    sg.ensure_workflow("default", "wf", "desc", {"terraformVersion": "1.5.7"})

    assert captured["body"]["WfType"] == "TERRAFORM"
    assert captured["body"]["TerraformConfig"] == {"terraformVersion": "1.5.7"}
    assert captured["body"]["Id"] == captured["body"]["ResourceName"] == "wf"


def test_conflict_on_create_is_success(monkeypatch):
    """Re-running the action against an existing workflow must not be an error."""
    sg = SGClient("https://api.example/api/v1", "acme", "sgo_x")
    monkeypatch.setattr(sg, "_request", lambda *a, **k: (409, {"msg": "already exists"}))

    assert sg.ensure_workflow("default", "wf", "d", {}) == 409
    assert sg.ensure_workflow_group("default") == 409


# --- auth --------------------------------------------------------------------------------------


def test_auth_header_uses_the_apikey_scheme(monkeypatch):
    """Matches sg-cli: `Authorization: apikey <token>`, not Bearer."""
    sg = SGClient("https://api.example/api/v1", "acme", "sgo_secret")
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["auth"] = request.get_header("Authorization")

        class _R:
            status = 200

            def read(self):
                return json.dumps({"msg": "ok"}).encode()

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        return _R()

    monkeypatch.setattr(client.urllib.request, "urlopen", fake_urlopen)

    sg._request("GET", "/wfgrps/")

    assert captured["auth"] == "apikey sgo_secret"


# --- run facts and cleanup ----------------------------------------------------------------------


def test_policy_results_follow_the_snake_case_signed_url(monkeypatch):
    """
    The facts endpoint returns `signed_url`; this used to read only `signedUrl` and so always
    returned {}. It went unnoticed for as long as the results artifact was covering for it.
    """
    sg = SGClient("https://api.example/api/v1", "acme", "sgo_x")
    monkeypatch.setattr(sg, "_request", lambda *a, **k: (200, {"msg": {"signed_url": "https://s3.example/facts"}}))

    class _R:
        def read(self):
            return json.dumps({"PolicyEvalResults": {"p": [{"result": "PASS"}]}}).encode()

        def info(self):
            return {}

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(client.urllib.request, "urlopen", lambda *a, **k: _R())

    assert sg.get_policy_results("default", "wf", "run-1") == {"p": [{"result": "PASS"}]}


def test_policy_results_accept_an_inline_payload(monkeypatch):
    sg = SGClient("https://api.example/api/v1", "acme", "sgo_x")
    monkeypatch.setattr(
        sg, "_request", lambda *a, **k: (200, {"msg": {"PolicyEvalResults": {"p": [{"result": "FAIL"}]}}})
    )

    assert sg.get_policy_results("default", "wf", "run-1") == {"p": [{"result": "FAIL"}]}


def test_missing_results_artifact_is_none_not_empty(monkeypatch):
    """
    The caller distinguishes "no such artifact, the facts are authoritative" from "the artifact
    exists and no policies matched". Collapsing both to {} would hide a real no-policies verdict.
    """
    sg = SGClient("https://api.example/api/v1", "acme", "sgo_x")
    monkeypatch.setattr(sg, "_request", lambda *a, **k: (404, {"msg": "not found"}))

    assert sg.get_results_artifact("default", "wf", "run-1/tirith-results.json") is None


@pytest.mark.parametrize("status", [200, 204, 404])
def test_delete_artifact_treats_absence_as_success(monkeypatch, status):
    """404 means someone already removed it, which is the state we wanted."""
    sg = SGClient("https://api.example/api/v1", "acme", "sgo_x")
    monkeypatch.setattr(sg, "_request", lambda *a, **k: (status, {}))

    assert sg.delete_artifact("default", "wf", "__sg.abc1234-default.tar.gz") is True


def test_delete_artifact_reports_failure_rather_than_raising(monkeypatch):
    """Cleanup runs after the verdict is known, so a failure must not change the outcome."""
    sg = SGClient("https://api.example/api/v1", "acme", "sgo_x")
    monkeypatch.setattr(sg, "_request", lambda *a, **k: (403, {"msg": "denied"}))

    assert sg.delete_artifact("default", "wf", "__sg.abc1234-default.tar.gz") is False


def test_delete_artifact_targets_a_single_path_segment(monkeypatch):
    """
    A nested name is swallowed by the greedy <path:wfGrp> converter in the authorizer and matches
    `DELETE .../wfgrps/<wfGrp>/` -- the workflow-group delete -- so it would be checked against
    entirely the wrong permission.
    """
    sg = SGClient("https://api.example/api/v1", "acme", "sgo_x")
    seen = {}
    monkeypatch.setattr(sg, "_request", lambda m, p, *a, **k: (seen.update(method=m, path=p), (200, {}))[1])

    sg.delete_artifact("default", "wf", "__sg.abc1234-default.tar.gz")

    assert seen["method"] == "DELETE"
    tail = seen["path"].split("/artifacts/", 1)[1].rstrip("/")
    assert "/" not in tail, f"artifact name must be one segment, got {tail!r}"


@pytest.mark.parametrize("folder", [None, ""])
def test_upload_archive_omits_an_unset_folder(monkeypatch, folder):
    """
    urlencode stringifies None to the literal "None", and the endpoint treats any non-empty value
    as a subfolder -- so passing it unconditionally created a real `None/` directory in S3 and left
    the archive at a nested key the post-run delete could not address. Caught in QA.
    """
    sg = SGClient("https://api.example/api/v1", "acme", "sgo_x")
    seen = {}
    monkeypatch.setattr(sg, "_request", lambda m, p, *a, **k: (seen.update(path=p), _upload_response())[1])
    monkeypatch.setattr(client.urllib.request, "urlopen", _ok_urlopen())

    sg.upload_file("default", "wf", "__sg.abc1234-default.tar.gz", folder, b"tarbytes")

    assert "folder=" not in seen["path"], seen["path"]
    assert "None" not in seen["path"], seen["path"]


def test_upload_archive_sends_a_folder_when_one_is_given(monkeypatch):
    sg = SGClient("https://api.example/api/v1", "acme", "sgo_x")
    seen = {}
    monkeypatch.setattr(sg, "_request", lambda m, p, *a, **k: (seen.update(path=p), _upload_response())[1])
    monkeypatch.setattr(client.urllib.request, "urlopen", _ok_urlopen())

    sg.upload_file("default", "wf", "a.tar.gz", "abc1234", b"tarbytes")

    assert "folder=abc1234" in seen["path"]


# --- publishing the state document ---------------------------------------------------------------


def test_upload_file_honours_a_json_content_type(monkeypatch):
    """
    The state document is JSON, not a gzip. S3 signs the content type into the URL, so sending the
    archive's type with a JSON body is a signature mismatch.
    """
    sg = SGClient("https://api.example/api/v1", "acme", "sgo_x")
    captured = {}

    def fake_request(method, path, **kwargs):
        captured["path"] = path
        return _upload_response()

    monkeypatch.setattr(sg, "_request", fake_request)
    uploaded = {}

    def fake_urlopen(request, timeout=None):
        uploaded["content_type"] = request.get_header("Content-type")
        uploaded["body"] = request.data

        class _R:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        return _R()

    monkeypatch.setattr(client.urllib.request, "urlopen", fake_urlopen)

    sg.upload_file("default", "wf", "tfstate.json", None, b'{"version": 4}', content_type="application/json")

    assert uploaded["content_type"] == "application/json"
    assert uploaded["body"] == b'{"version": 4}'
    # And the same type is what the URL was signed for.
    assert "contentType=application%2Fjson" in captured["path"]


def test_manages_terraform_state_reads_the_workflow_config(monkeypatch):
    sg = SGClient("https://api.example/api/v1", "acme", "sgo_x")

    monkeypatch.setattr(
        sg, "_request", lambda *a, **k: (200, {"msg": {"TerraformConfig": {"managedTerraformState": True}}})
    )
    assert sg.manages_terraform_state("default", "wf") is True

    monkeypatch.setattr(
        sg, "_request", lambda *a, **k: (200, {"msg": {"TerraformConfig": {"managedTerraformState": False}}})
    )
    assert sg.manages_terraform_state("default", "wf") is False


@pytest.mark.parametrize(
    "response",
    [
        (404, {"msg": "not found"}),
        (500, {"msg": "boom"}),
        (200, {"msg": "a string, not a dict"}),
        (200, {}),
    ],
)
def test_an_unreadable_workflow_is_treated_as_managing_its_own_state(monkeypatch, response):
    """
    Fails safe. Not being able to tell whether `artifacts/tfstate.json` is live terraform state is
    not a reason to overwrite it with a masked document.
    """
    sg = SGClient("https://api.example/api/v1", "acme", "sgo_x")
    monkeypatch.setattr(sg, "_request", lambda *a, **k: response)

    assert sg.manages_terraform_state("default", "wf") is True
