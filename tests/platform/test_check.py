"""
Tests for the check orchestration.

Focused on `upload_state_document`, because that is the one place in this codebase that can overwrite
a customer's live terraform state. `artifacts/tfstate.json` is not just a name we picked: the
managed-state backend writes it, state locking keys on the literal basename, and the state-backends
view lists it. Writing a *masked* document there for a workflow that manages its own state would be
data loss, so the guard is asserted rather than assumed.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))

from tirith.platform import check
from tirith.platform.client import SGError


class FakeClient:
    def __init__(self, managed=False, fail=False):
        self.managed = managed
        self.fail = fail
        self.uploads = []

    def manages_terraform_state(self, wfgrp, workflow_id):
        return self.managed

    def upload_file(self, wfgrp, workflow_id, filename, folder, content, content_type=None):
        if self.fail:
            raise SGError("presigned URL expired")
        self.uploads.append(
            {
                "filename": filename,
                "folder": folder,
                "content": content,
                "content_type": content_type,
            }
        )
        return f"orgs/acme/wfs/K/artifacts/{filename}"


class Opts:
    workflow_group = "default"
    workflow_id = "wf"


STATE = {
    "version": 4,
    "resources": [{"type": "aws_s3_bucket", "instances": [{"attributes": {"b": "__SG_REDACTED__"}}]}],
}


def test_the_state_is_published_as_tfstate_json():
    client = FakeClient(managed=False)

    check.upload_state_document(client, Opts(), STATE)

    assert len(client.uploads) == 1
    upload = client.uploads[0]
    assert upload["filename"] == "tfstate.json"
    # The artifacts root, not a subfolder: that is the key the platform reads.
    assert upload["folder"] is None
    assert upload["content_type"] == "application/json"
    assert json.loads(upload["content"].decode()) == STATE


def test_the_state_is_not_written_over_a_managed_state_workflow(capsys):
    """The data-loss guard. That object is the live state for such a workflow."""
    client = FakeClient(managed=True)

    check.upload_state_document(client, Opts(), STATE)

    assert client.uploads == []
    warning = capsys.readouterr().err
    assert "manages its own terraform state" in warning
    # And it says the state is still evaluated, so the skip does not read as a lost check.
    assert "still evaluated" in warning


def test_a_failed_publish_is_a_warning_not_a_failure(capsys):
    """
    The verdict does not depend on this upload. A run whose policies evaluated perfectly well must not
    go red because a best-effort convenience copy could not be written.
    """
    client = FakeClient(managed=False, fail=True)

    check.upload_state_document(client, Opts(), STATE)

    assert "could not publish tfstate.json" in capsys.readouterr().err


def test_the_published_state_is_flagged_as_masked(capsys):
    """
    A file at the canonical state key that looks like state but is full of __SG_REDACTED__ is a
    footgun for whoever downloads it next, so the log says so.
    """
    check.upload_state_document(FakeClient(managed=False), Opts(), STATE)

    assert "cannot be used to run terraform" in capsys.readouterr().err


def test_the_state_document_name_matches_the_one_inside_the_archive():
    """
    The step reads the archive copy to publish TfStateCleaned while the platform reads the uploaded
    one. Two different names would be two sources of truth for the same thing.
    """
    from tirith.platform import archive

    assert check.STATE_DOCUMENT_NAME == archive.STATE_DOCUMENT


# --- packing: the source is uploaded, but never at the cost of the gate --------------------------
#
# The source tree is packed by default, so an exclusion that does not fire -- a committed vendor
# directory, a build output tree -- would otherwise turn a working policy check into a failed run.
# That trade is the wrong way round: the verdict gates the merge, the source is a convenience for
# whatever reads the bundle afterwards.


def _tree(tmp_path, extra_bytes=0):
    source = tmp_path / "src"
    source.mkdir()
    (source / "main.tf").write_text('resource "null_resource" "a" {}\n')
    if extra_bytes:
        # Random, so gzip cannot make it disappear.
        (source / "vendor.bin").write_bytes(os.urandom(extra_bytes))
    return str(source)


def test_the_source_is_packed_on_the_normal_path(tmp_path):
    archive_bytes, manifest, skipped = check.pack_documents(_tree(tmp_path), {"masked": True}, None, None)

    assert manifest["files"] == 1
    assert manifest["documents"] == ["plan.json"]
    assert skipped is None
    assert archive_bytes


def test_an_oversized_source_tree_degrades_to_documents_only(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(check.archive, "MAX_ARCHIVE_BYTES", 50 * 1024)

    archive_bytes, manifest, skipped = check.pack_documents(
        _tree(tmp_path, extra_bytes=200_000), {"masked": True}, None, None
    )

    # The documents still go, so the policies still run.
    assert manifest["documents"] == ["plan.json"]
    assert manifest["files"] == 0
    # And the caller can tell that the bundle has no code in it.
    assert skipped and "over the" in skipped

    warning = capsys.readouterr().err
    assert "carries no code" in warning
    assert "--source-dir" in warning


def test_an_oversized_documents_only_archive_still_fails(tmp_path, monkeypatch):
    """
    Nothing left to drop. Degrading further would mean uploading an archive with no documents, which
    is not a check at all -- so this stays fatal rather than becoming a silent pass.
    """
    monkeypatch.setattr(check.archive, "MAX_ARCHIVE_BYTES", 50 * 1024)

    with pytest.raises(check.archive.ArchiveError):
        check.pack_documents(None, {"blob": os.urandom(200_000).hex()}, None, None)


def test_the_size_message_is_readable_below_a_megabyte(monkeypatch):
    """
    Integer MB division reported everything small as "0 MB over the 0 MB limit". That message is now
    surfaced on a pull request, where it has to mean something.
    """
    from tirith.platform.archive import _human_bytes

    assert _human_bytes(137 * 1024 * 1024) == "137.0 MB"
    assert _human_bytes(300 * 1024) == "300.0 KB"
    assert _human_bytes(512) == "512 bytes"


def test_the_policy_step_is_spliced_in_as_a_pre_plan_step():
    """
    The whole mechanism, and it uses only primitives the platform already had: core splices
    `prePlanWfStepsConfig` ahead of `generate-terraform-plan`, and the step exits 12, which tells the
    run controller to complete the run and skip everything after it. So core needs to know nothing
    about this feature -- which is why there is no terraform action for it.
    """
    config = check.terraform_config("1.5.7", None)

    steps = config["prePlanWfStepsConfig"]
    assert len(steps) == 1
    assert steps[0]["name"] == check.POLICY_STEP_NAME
    assert steps[0]["wfStepTemplateId"] == check.POLICY_STEP_TEMPLATE
    # Every input the step needs travels in its own step input, not the terraform configuration.
    assert steps[0]["wfStepInputData"]["schemaType"] == "FORM_JSONSCHEMA"
    # A policy check writes no state, so it must not take a managed-state backend override.
    assert config["managedTerraformState"] is False
    # No stored input kind: routing is by which document is in the archive.
    assert "policyInputKind" not in config


def test_a_step_template_override_is_honoured():
    config = check.terraform_config("1.5.7", "/demo-org/tirith-iac-governance:3")

    assert config["prePlanWfStepsConfig"][0]["wfStepTemplateId"] == "/demo-org/tirith-iac-governance:3"


# --- the bundle is named per commit, and per RUN ------------------------------------------------
#
# A name shared by every run of the workflow is one two concurrent runs can overwrite, and the action
# derives a single workflow id per repository -- so two open pull requests, the ordinary case, would
# have one run evaluating the other's code and reporting the verdict as its own. Silently, on a merge
# gate. Naming it per commit removes the collision rather than detecting it afterwards.
#
# That is only possible because the name travels per RUN: core merges the run's TerraformConfig over
# the workflow's, so `prePlanWfStepsConfig` can differ every time. The workflow's stored copy is
# written once, at creation, and never updated.


def test_the_bundle_name_carries_the_commit():
    from tirith.platform.client import ARCHIVE_NAME_TEMPLATE

    name = ARCHIVE_NAME_TEMPLATE.format(sha="a1b2c3d", tag="plan")

    assert name == "tirith-bundle-a1b2c3d-plan.tar.gz"
    # Two commits cannot collide, which is the entire point.
    assert name != ARCHIVE_NAME_TEMPLATE.format(sha="9999999", tag="plan")


def test_the_bundle_name_survives_the_artifact_syncs_exclude_list():
    """
    The sync is the delivery mechanism, so a name matching any of its excludes would be dropped
    silently and never reach the container. `__sg.`, which this name used to carry, is excluded
    precisely so the old carrier stayed OUT of the sync -- exactly wrong now.
    """
    import fnmatch

    from tirith.platform.client import ARCHIVE_NAME_TEMPLATE

    name = ARCHIVE_NAME_TEMPLATE.format(sha="a1b2c3d", tag="plan")
    excluded = ("sg.*", "__sg.*", "*__sg.*", "*pci_*", "*_thrifty_*", "*_gdpr_*", "*compliance_raw*")

    for pattern in excluded:
        assert not fnmatch.fnmatch(name, pattern), f"the bundle name matches the sync exclude {pattern!r}"
    assert name != "tfstate.json", "that name is a managed-state workflow's live state"


def test_the_run_names_its_own_bundle():
    """
    The per-run half. `wfStepInputData` on the *workflow* is written once and never updated, so the
    name has to be re-sent with each run for it to describe that run's commit.
    """
    step = check.policy_step(None, "tirith-bundle-a1b2c3d-plan.tar.gz")

    assert step["wfStepInputData"]["data"]["bundlePath"] == "tirith-bundle-a1b2c3d-plan.tar.gz"
    # Sent in full: core's merge is shallow, so supplying prePlanWfStepsConfig replaces the whole
    # list and a partial entry would lose the template id the step runs from.
    assert step["wfStepTemplateId"] == check.POLICY_STEP_TEMPLATE
    assert step["name"] == check.POLICY_STEP_NAME
    assert step["timeout"] == check.POLICY_STEP_TIMEOUT


def test_the_step_template_override_reaches_the_per_run_step():
    step = check.policy_step("/demo-org/tirith-iac-governance:3", "b.tar.gz")

    assert step["wfStepTemplateId"] == "/demo-org/tirith-iac-governance:3"


def test_the_run_tells_the_step_whether_state_is_managed():
    """
    The step writes the masked state to `artifacts/tfstate.json`, which for a managed-state workflow is
    the LIVE state. It must be told, and told explicitly rather than left to a default: a missing key
    that happens to mean "not managed" is one refactor away from meaning the opposite.
    """
    step = check.policy_step(None, "tirith-bundle-a1b2c3d-plan.tar.gz")

    data = step["wfStepInputData"]["data"]
    assert data["managedTerraformState"] is False


def test_the_workflow_never_takes_a_managed_state_backend():
    """And the claim the passthrough rests on: these workflows do not manage state in the first place."""
    config = check.terraform_config("1.5.7", None)

    assert config["managedTerraformState"] is False
