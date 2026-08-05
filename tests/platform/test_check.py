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
