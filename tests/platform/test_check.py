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


STATE = {"version": 4, "resources": [{"type": "aws_s3_bucket", "instances": [{"attributes": {"b": "__SG_REDACTED__"}}]}]}


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
    archive_bytes, manifest, skipped = check.pack_documents(
        _tree(tmp_path), {"masked": True}, None, None
    )

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
