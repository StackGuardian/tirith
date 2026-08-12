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


# --- metadata.json: the provenance half -----------------------------------------------------------
#
# Two shapes have to produce an honest document: a CI run, where the trigger payload carries the
# repository and commit, and a bare local invocation, where none of it exists. The local case is the
# one worth guarding -- the temptation is to fill the gaps from the environment, and a fabricated
# repository in a file that outlives the run is worse than a null.


class MetaOpts:
    trigger_details = {"type": "cli"}
    repo_url = None
    repo_ref = None
    repo_path = None
    sha = None
    source_dir = None
    input_kind = "terraform_plan"
    org = "acme"
    workflow_group = "default"
    workflow_id = "infra"
    artifact_tag = "default"


def _opts(**overrides):
    opts = MetaOpts()
    for key, value in overrides.items():
        setattr(opts, key, value)
    return opts


def test_a_local_run_states_it_is_local_rather_than_leaving_ci_to_be_inferred():
    metadata = check.build_metadata(_opts(), redactions=0)

    assert metadata["origin"] == {"kind": "local", "trigger_type": "cli", "ci_run_url": None}
    # Nulls, not omissions, and nothing invented.
    assert metadata["repository"]["provider"] == "unknown"
    assert metadata["repository"]["url"] is None
    assert metadata["repository"]["commit"] is None
    assert metadata["repository"]["change_request"] is None
    assert metadata["schema_version"] == check.METADATA_SCHEMA_VERSION


def test_a_ci_run_records_the_repository_and_the_change_request():
    opts = _opts(
        trigger_details={
            "type": "tirith",
            "repoHttpUrl": "https://github.com/acme/infra",
            "headSha": "9f2c1ab5",
            "ref": "feat/rds",
            "prId": "412",
            "eventSource": "https://github.com/acme/infra/pull/412",
            "runUrl": "https://github.com/acme/infra/actions/runs/1",
        }
    )

    metadata = check.build_metadata(opts, redactions=12)

    assert metadata["origin"]["kind"] == "ci"
    assert metadata["repository"]["provider"] == "github"
    assert metadata["repository"]["commit"] == "9f2c1ab5"
    assert metadata["repository"]["change_request"]["id"] == "412"
    assert metadata["masking"]["redactions"] == 12


def test_a_credential_in_the_repo_url_never_reaches_the_metadata():
    """
    `https://x-access-token:ghs_…@github.com/…` is an ordinary value for a CI checkout to hold, and
    GitLab's own CI_REPOSITORY_URL embeds a job token the same way. This file ships inside the bundle
    and outlives the run, so a token written here is a token persisted in an artifact.
    """
    import json as _json

    opts = _opts(repo_url="https://x-access-token:ghs_verysecret@github.com/acme/infra.git")

    metadata = check.build_metadata(opts, redactions=0)

    assert "ghs_verysecret" not in _json.dumps(metadata)
    assert "x-access-token" not in _json.dumps(metadata)
    assert metadata["repository"]["url"] == "https://github.com/acme/infra.git"
    assert metadata["repository"]["host"] == "github.com"


def test_an_scp_style_remote_still_yields_a_host():
    """`git@github.com:acme/infra.git` has no scheme, so urlsplit reads it as a path with no host."""
    metadata = check.build_metadata(_opts(repo_url="git@github.com:acme/infra.git"), redactions=0)

    assert metadata["repository"]["host"] == "github.com"
    assert metadata["repository"]["provider"] == "github"


def test_a_self_hosted_host_is_unknown_rather_than_guessed():
    """Guessing `github` for git.example.internal would be worse than admitting we cannot tell."""
    metadata = check.build_metadata(_opts(repo_url="https://git.example.internal/acme/infra"), redactions=0)

    assert metadata["repository"]["provider"] == "unknown"
    # The raw host is still recorded, which is what makes the honest answer useful.
    assert metadata["repository"]["host"] == "git.example.internal"


def test_the_declared_repo_path_wins_over_inference():
    opts = _opts(source_dir=".", repo_path="infra/prod")

    code = check.build_metadata(opts, redactions=0)["code"]

    assert code["repo_path"] == "infra/prod"
    assert code["repo_path_from"] == "flag"


def test_the_repo_path_is_inferred_from_the_enclosing_checkout(tmp_path):
    """
    Inference walks up for a `.git` entry rather than shelling out -- this package has no git
    dependency, and a `.git` *file* (worktrees, submodules) has to count too.
    """
    (tmp_path / ".git").write_text("gitdir: /elsewhere")
    nested = tmp_path / "infra" / "prod"
    nested.mkdir(parents=True)

    code = check.build_metadata(_opts(source_dir=str(nested)), redactions=0)["code"]

    assert code["repo_path"] == "infra/prod"
    assert code["repo_path_from"] == "git_root"


def test_the_repository_root_is_the_empty_string_not_a_dot(tmp_path):
    """
    `""` means the root and joins correctly; `None` means "we could not tell". Collapsing them would
    make a consumer unable to distinguish a root-level project from an unknown one.
    """
    (tmp_path / ".git").mkdir()

    code = check.build_metadata(_opts(source_dir=str(tmp_path)), redactions=0)["code"]

    assert code["repo_path"] == ""
    assert code["repo_path_from"] == "git_root"


def test_an_unlocatable_repository_root_says_so(tmp_path):
    code = check.build_metadata(_opts(source_dir=str(tmp_path)), redactions=0)["code"]

    assert code["repo_path"] is None
    assert code["repo_path_from"] is None


def test_the_oversize_retry_records_that_the_code_was_dropped_for_size(tmp_path, monkeypatch):
    """
    The fallback re-packs without the source. A consumer holding only the bundle must be able to tell
    that from a deliberate documents-only run, which is the difference between "nothing to fix here"
    and "we could not show you the code".
    """
    import io
    import json as _json
    import tarfile

    monkeypatch.setattr(check.archive, "MAX_ARCHIVE_BYTES", 50 * 1024)
    source = tmp_path / "src"
    source.mkdir()
    (source / "main.tf").write_text("")
    (source / "vendor.bin").write_bytes(os.urandom(200_000))

    archive_bytes, _manifest, reason = check.pack_documents(
        str(source),
        {"masked": True},
        None,
        None,
        metadata={"schema_version": 1, "code": {}},
    )

    assert reason
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tar:
        metadata = _json.loads(tar.extractfile(check.archive.METADATA_DOCUMENT).read())
    assert metadata["code"]["absent_reason"] == "too_large"
    assert metadata["code"]["present"] is False


def test_a_declared_repo_path_cannot_escape_the_repository(tmp_path, capsys):
    """
    `--repo-path ../..` used to survive `strip("/")` and be recorded verbatim.

    The single use of this field is a consumer joining it to write files back into the repository it
    thinks it is patching, so a value that climbs out of the tree is the one shape that must not be
    recorded. Refused and left absent rather than recorded wrong -- absent is a state consumers already
    handle.
    """
    for escaping in ("../..", "/etc", "infra/../../elsewhere"):
        code = check.build_metadata(_opts(source_dir=str(tmp_path), repo_path=escaping), redactions=0)["code"]

        assert code["repo_path"] != escaping
        assert code["repo_path"] is None or not code["repo_path"].startswith("..")
    assert "must be a path inside the repository" in capsys.readouterr().err


def test_a_declared_repo_path_is_normalised(tmp_path):
    """Leading and trailing slashes, and a redundant `.`, all describe the same location."""
    for declared, expected in (("/infra/prod/", "infra/prod"), ("./infra", "infra"), (".", ""), ("/", "")):
        code = check.build_metadata(_opts(source_dir=str(tmp_path), repo_path=declared), redactions=0)["code"]
        assert code["repo_path"] == expected, f"{declared!r} -> {code['repo_path']!r}"
        assert code["repo_path_from"] == "flag"


def test_a_nonexistent_source_dir_fails_rather_than_degrading(tmp_path):
    """
    `archive.pack` raises ArchiveError for a missing directory *and* for an oversized archive, and the
    degrade path only knew about the second. A typo'd `--source-dir` therefore reported "the tree was
    too large", dropped the code and completed the run -- a check that passed having evaluated no
    source at all, with the bundle's own metadata stating the wrong reason.
    """
    with pytest.raises(check.CheckError, match="--source-dir does not exist"):
        check.pack_documents(
            str(tmp_path / "no-such-dir"),
            {"masked": True},
            None,
            None,
            metadata={"schema_version": 1, "code": {}},
        )
