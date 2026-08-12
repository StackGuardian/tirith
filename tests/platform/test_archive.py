"""
Tests for the project archive.

The assertions that matter read the bytes *inside the built tarball*, not the objects handed to
pack(). That distinction is the whole point: a previous iteration of this code masked a plan
correctly in memory and still shipped the plaintext, because the secret lived in a second place
nobody had looked at. Asserting on the input would have passed.
"""

import io
import json
import os
import tarfile

import pytest

from tirith.platform import archive

SECRET = "hunter2-this-must-never-leave-the-runner"


def members(archive_bytes):
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tar:
        return sorted(tar.getnames())


def read_member(archive_bytes, name):
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tar:
        return tar.extractfile(name).read()


def raw_bytes(archive_bytes):
    """Everything in the archive, decompressed, as one blob -- for leak assertions."""
    blob = b""
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tar:
        for member in tar.getmembers():
            blob += member.name.encode()
            if member.isfile():
                blob += tar.extractfile(member).read()
    return blob


# --- documents ---------------------------------------------------------------------------------


def test_documents_land_at_the_fixed_names_the_step_looks_for(tmp_path):
    body, _manifest = archive.pack(source_dir=None, plan={"a": 1}, state={"b": 2}, infracost={"c": 3})

    assert members(body) == ["infracost.json", "plan.json", "tfstate.json"]
    assert json.loads(read_member(body, "plan.json")) == {"a": 1}


def test_absent_documents_are_simply_not_written():
    body, _manifest = archive.pack(source_dir=None, state={"version": 4})

    assert members(body) == ["tfstate.json"]


def test_masked_document_wins_over_a_stale_file_on_disk(tmp_path):
    """
    The dangerous ordering: a plan.json left in the working directory from an earlier run would
    otherwise be packed *and* the masked one written, shipping both.
    """
    (tmp_path / "plan.json").write_text(json.dumps({"leaked": SECRET}))

    body, _manifest = archive.pack(source_dir=str(tmp_path), plan={"masked": "__SG_REDACTED__"})

    assert json.loads(read_member(body, "plan.json")) == {"masked": "__SG_REDACTED__"}
    assert SECRET.encode() not in raw_bytes(body)


@pytest.mark.parametrize("name", ["plan.json", "tfstate.json", "infracost.json"])
def test_reserved_names_on_disk_are_never_packed(tmp_path, name):
    """
    The leak this closes: `terraform state pull > state.json` is the documented way to produce a
    state file, so one routinely sits in the working directory -- raw and unmasked. Packing the
    source tree naively shipped it in full, right next to the masked copy.

    These names are only ever written by pack() from an already-masked object. A caller who wants
    the file evaluated passes --state-path / --input-path, which masks it first.
    """
    (tmp_path / name).write_text(json.dumps({"outputs": {"db": {"value": SECRET}}}))
    (tmp_path / "main.tf").write_text("")

    body, _manifest = archive.pack(source_dir=str(tmp_path), plan={"masked": True})

    assert SECRET.encode() not in raw_bytes(body)
    assert members(body) == ["code/main.tf", "plan.json"]


@pytest.mark.parametrize("name", ["tfplan.json", "state.json", "terraform.plan.json"])
def test_the_file_a_document_was_read_from_is_never_packed(tmp_path, name):
    """
    Reserving only the three names pack() writes was not enough. The input is routinely called
    something else -- `tfplan.json` is the second name discovery accepts, and
    `terraform state pull > state.json` is the documented way to produce state -- so the source walk
    shipped the unmasked original one filename away from the masked copy.
    """
    (tmp_path / name).write_text(json.dumps({"outputs": {"db": {"value": SECRET}}}))
    (tmp_path / "main.tf").write_text("")

    body, _manifest = archive.pack(
        source_dir=str(tmp_path),
        plan={"masked": True},
        document_sources=(str(tmp_path / name),),
    )

    assert SECRET.encode() not in raw_bytes(body)
    assert members(body) == ["code/main.tf", "plan.json"]


def test_the_binary_plan_is_never_packed(tmp_path):
    """
    A binary plan embeds the prior state, so it carries every attribute of every existing resource
    in plaintext -- worse than a raw state file, and it matches none of the *.tfstate patterns.
    --plan-file converts and masks it in memory, which the source walk then undid.
    """
    (tmp_path / "tfplan").write_bytes(b"\x1f\x8b binary plan " + SECRET.encode())
    (tmp_path / "prod.tfplan").write_bytes(SECRET.encode())
    (tmp_path / "main.tf").write_text("")

    body, _manifest = archive.pack(source_dir=str(tmp_path), plan={"masked": True})

    assert SECRET.encode() not in raw_bytes(body)
    assert members(body) == ["code/main.tf", "plan.json"]


def test_a_document_source_outside_the_tree_excludes_nothing(tmp_path):
    """
    An out-of-tree path cannot collide with a member name, so it must not be reduced to a bare
    basename -- doing so would silently drop an unrelated same-named file from the archive.
    """
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (outside / "main.tf").write_text("")
    source = tmp_path / "src"
    source.mkdir()
    (source / "main.tf").write_text("resource {}")

    body, _manifest = archive.pack(
        source_dir=str(source),
        plan={"masked": True},
        document_sources=(str(outside / "main.tf"),),
    )

    assert members(body) == ["code/main.tf", "plan.json"]
    assert read_member(body, "code/main.tf") == b"resource {}"


def test_masked_document_is_what_gets_written(tmp_path):
    """The counterpart: a supplied document really does reach the archive."""
    (tmp_path / "tfstate.json").write_text(json.dumps({"secret": SECRET}))

    body, _manifest = archive.pack(source_dir=str(tmp_path), state={"masked": True})

    assert json.loads(read_member(body, "tfstate.json")) == {"masked": True}
    assert SECRET.encode() not in raw_bytes(body)


# --- exclusions --------------------------------------------------------------------------------


def test_terraform_provider_cache_is_excluded(tmp_path):
    """A provider cache is routinely hundreds of MB; shipping it would make every run unusable."""
    provider = tmp_path / ".terraform" / "providers" / "registry.terraform.io"
    provider.mkdir(parents=True)
    (provider / "terraform-provider-aws").write_bytes(b"x" * 1024)
    (tmp_path / "main.tf").write_text('resource "null_resource" "a" {}')

    body, manifest = archive.pack(source_dir=str(tmp_path))

    assert members(body) == ["code/main.tf"]
    assert manifest["skipped"] >= 1


def test_git_directory_is_excluded(tmp_path):
    """.git carries full history, so anything ever committed would ship."""
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text(f"token = {SECRET}")
    (tmp_path / "main.tf").write_text("")

    body, _manifest = archive.pack(source_dir=str(tmp_path))

    assert members(body) == ["code/main.tf"]
    assert SECRET.encode() not in raw_bytes(body)


@pytest.mark.parametrize("name", ["terraform.tfstate", "terraform.tfstate.backup", "prod.tfstate"])
def test_raw_state_files_are_excluded(tmp_path, name):
    """
    Raw state is unmasked by definition. Left in, it would travel next to the masked copy and
    undo the masking entirely.
    """
    (tmp_path / name).write_text(json.dumps({"outputs": {"db": {"value": SECRET}}}))
    (tmp_path / "main.tf").write_text("")

    body, _manifest = archive.pack(source_dir=str(tmp_path))

    assert f"code/{name}" not in members(body)
    assert SECRET.encode() not in raw_bytes(body)


def test_gitignore_is_honoured(tmp_path):
    (tmp_path / ".gitignore").write_text("secrets.auto.tfvars\nbuild/\n")
    (tmp_path / "secrets.auto.tfvars").write_text(f'password = "{SECRET}"')
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "out.bin").write_text("junk")
    (tmp_path / "main.tf").write_text("")

    body, _manifest = archive.pack(source_dir=str(tmp_path))

    assert "code/secrets.auto.tfvars" not in members(body)
    assert "code/build/out.bin" not in members(body)
    assert SECRET.encode() not in raw_bytes(body)


def test_gitignore_can_be_turned_off(tmp_path):
    (tmp_path / ".gitignore").write_text("keep-me.tf\n")
    (tmp_path / "keep-me.tf").write_text("")

    body, _manifest = archive.pack(source_dir=str(tmp_path), respect_gitignore=False)

    assert "code/keep-me.tf" in members(body)


def test_extra_excludes_are_applied(tmp_path):
    (tmp_path / "big.zip").write_text("junk")
    (tmp_path / "main.tf").write_text("")

    body, _manifest = archive.pack(source_dir=str(tmp_path), extra_excludes=("*.zip",))

    assert members(body) == ["code/main.tf"]


def test_lock_file_is_kept(tmp_path):
    """It pins provider versions, is small, and the run controller's init wants it."""
    (tmp_path / ".terraform.lock.hcl").write_text("provider ...")

    body, _manifest = archive.pack(source_dir=str(tmp_path))

    assert "code/.terraform.lock.hcl" in members(body)


def test_symlinks_are_skipped(tmp_path):
    """A symlink out of the tree either breaks on extraction or smuggles a file in."""
    outside = tmp_path.parent / "outside.txt"
    outside.write_text(SECRET)
    source = tmp_path / "src"
    source.mkdir()
    (source / "main.tf").write_text("")
    os.symlink(str(outside), str(source / "link.txt"))

    body, _manifest = archive.pack(source_dir=str(source))

    assert members(body) == ["code/main.tf"]
    assert SECRET.encode() not in raw_bytes(body)


# --- structure ---------------------------------------------------------------------------------


def test_nested_directories_keep_their_relative_paths(tmp_path):
    (tmp_path / "modules" / "vpc").mkdir(parents=True)
    (tmp_path / "modules" / "vpc" / "main.tf").write_text("")
    (tmp_path / "main.tf").write_text("")

    body, _manifest = archive.pack(source_dir=str(tmp_path))

    assert "code/modules/vpc/main.tf" in members(body)


def test_no_source_dir_is_allowed():
    """--no-source: send only the documents."""
    body, manifest = archive.pack(source_dir=None, plan={"a": 1})

    assert members(body) == ["plan.json"]
    assert manifest["files"] == 0


def test_missing_source_dir_is_an_error(tmp_path):
    with pytest.raises(archive.ArchiveError):
        archive.pack(source_dir=str(tmp_path / "does-not-exist"))


def test_oversized_archive_is_refused(tmp_path, monkeypatch):
    """
    Failing loudly beats a five-minute upload that times out the run. A runaway archive is nearly
    always an exclusion that did not fire.
    """
    monkeypatch.setattr(archive, "MAX_ARCHIVE_BYTES", 512)
    (tmp_path / "big.tf").write_text("resource {}\n" * 20000)

    with pytest.raises(archive.ArchiveError, match="limit"):
        archive.pack(source_dir=str(tmp_path))


def test_manifest_reports_what_went_in(tmp_path):
    (tmp_path / "main.tf").write_text("")
    (tmp_path / ".terraform").mkdir()
    (tmp_path / ".terraform" / "x").write_text("")

    _body, manifest = archive.pack(source_dir=str(tmp_path), plan={"a": 1})

    assert manifest["files"] == 1
    assert manifest["documents"] == ["plan.json"]
    assert manifest["skipped"] >= 1
    assert manifest["bytes"] > 0


def test_the_binary_plan_that_plan_file_read_is_never_packed(tmp_path):
    """
    --plan-file converts the binary plan in memory precisely so nothing unmasked touches the disk --
    but the binary plan is already on disk, and it embeds the prior state: every attribute of every
    existing resource. The `tfplan` name patterns only cover the spellings the README uses, and
    `terraform plan -out=plan.out` is at least as common.
    """
    (tmp_path / "plan.out").write_bytes(b"binary plan " + SECRET.encode())
    (tmp_path / "main.tf").write_text("")

    body, _manifest = archive.pack(
        source_dir=str(tmp_path),
        plan={"masked": True},
        document_sources=(str(tmp_path / "plan.out"),),
    )

    assert SECRET.encode() not in raw_bytes(body)
    assert members(body) == ["code/main.tf", "plan.json"]


# --- layout: code/ is a prefix, the root belongs to the documents -------------------------------


def test_the_source_lives_under_the_code_prefix(tmp_path):
    """
    The layout is a contract for whatever reads the bundle: source under `code/`, documents at the
    root, and `code/x` maps back to `<repo_path>/x`.
    """
    (tmp_path / "main.tf").write_text("")
    (tmp_path / "modules" / "vpc").mkdir(parents=True)
    (tmp_path / "modules" / "vpc" / "main.tf").write_text("")

    body, _manifest = archive.pack(source_dir=str(tmp_path), plan={"masked": True})

    assert members(body) == ["code/main.tf", "code/modules/vpc/main.tf", "plan.json"]


def test_the_documents_are_at_the_archive_root_and_never_under_a_prefix(tmp_path):
    """
    The one layout mistake that would not fail loudly.

    The step finds its inputs with a flat join onto the extraction directory and treats absence as
    normal (`_discover_document` returns None). So a document moved under `code/` -- or under any
    prefix -- would not raise: every policy would come back unevaluated and the run would report as
    passed-with-warnings. Nothing downstream distinguishes that from a genuinely clean plan, which is
    why this is asserted here rather than trusted.
    """
    (tmp_path / "main.tf").write_text("")

    body, _manifest = archive.pack(
        source_dir=str(tmp_path),
        plan={"masked": True},
        state={"masked": True},
        infracost={"masked": True},
    )

    for document in (archive.PLAN_DOCUMENT, archive.STATE_DOCUMENT, archive.INFRACOST_DOCUMENT):
        assert document in members(body), f"{document} must be at the archive root"
    assert not [name for name in members(body) if name.endswith(f"/{archive.PLAN_DOCUMENT}")]


def test_a_committed_document_name_is_still_skipped_under_the_prefix(tmp_path):
    """
    The reservation is a leak guard, and it stopped being self-evident when the prefix arrived.

    Under the old flat layout a committed `tfstate.json` would have collided with the masked one, so
    skipping it looked obviously necessary. `code/tfstate.json` cannot collide with anything -- and is
    still raw, unmasked state, which is the actual reason for the skip. Deleting it because "the
    collision is impossible now" is the mistake this test exists to catch.
    """
    (tmp_path / "tfstate.json").write_text(json.dumps({"secret": SECRET}))
    (tmp_path / "main.tf").write_text("")

    body, _manifest = archive.pack(source_dir=str(tmp_path), state={"masked": True})

    assert "code/tfstate.json" not in members(body)
    assert SECRET.encode() not in raw_bytes(body)


def test_metadata_is_absent_unless_asked_for(tmp_path):
    """A caller that supplies no metadata gets no member, so old bundles stay describable as such."""
    (tmp_path / "main.tf").write_text("")

    body, _manifest = archive.pack(source_dir=str(tmp_path))

    assert archive.METADATA_DOCUMENT not in members(body)


# --- metadata.json: what pack() observes, as opposed to what it was told ------------------------


def _metadata(archive_bytes):
    return json.loads(read_member(archive_bytes, archive.METADATA_DOCUMENT))


def test_metadata_records_what_was_actually_packed(tmp_path):
    """
    The counts come from the walk, not from the caller. "Claims code, packed nothing" is only
    detectable because this half of the document is produced here.
    """
    (tmp_path / "main.tf").write_text("")
    (tmp_path / "notes.txt").write_text("")

    body, _manifest = archive.pack(
        source_dir=str(tmp_path),
        plan={"masked": True},
        metadata={"schema_version": 1, "code": {"repo_path": "infra/prod", "repo_path_from": "flag"}},
    )

    code = _metadata(body)["code"]
    assert code["present"] is True
    assert code["prefix"] == "code/"
    assert code["files"] == 2
    assert code["repo_path"] == "infra/prod"
    assert _metadata(body)["documents"] == {"plan": "plan.json", "state": None, "infracost": None}


def test_metadata_cannot_claim_code_the_archive_does_not_carry(tmp_path):
    """
    `present` means "there are members under the prefix", not "a source directory was requested".

    Nothing writes an explicit directory entry, so a tree whose every file was excluded leaves no
    `code/` in the tar at all. A consumer comparing the tar against the metadata must never find them
    disagreeing, so the flag is derived from the count rather than from the request.
    """
    (tmp_path / "everything.tfstate").write_text("raw state")

    body, _manifest = archive.pack(
        source_dir=str(tmp_path),
        plan={"masked": True},
        metadata={"schema_version": 1, "code": {"repo_path": "infra", "repo_path_from": "flag"}},
    )

    code = _metadata(body)["code"]
    assert code["present"] is False
    assert code["prefix"] is None
    assert code["files"] == 0
    # And the path is withdrawn: there is nothing for it to describe.
    assert code["repo_path"] is None
    assert code["absent_reason"] == "empty_after_excludes"
    assert not [name for name in members(body) if name.startswith("code/")]


def test_metadata_says_why_no_source_was_requested(tmp_path):
    """
    A documents-only bundle has to distinguish "none wanted" from "dropped for size", or a consumer
    cannot tell a deliberate configuration from a truncated one.
    """
    body, _manifest = archive.pack(
        source_dir=None,
        plan={"masked": True},
        metadata={"schema_version": 1, "code": {"absent_reason": "not_requested"}},
    )

    code = _metadata(body)["code"]
    assert code["present"] is False
    assert code["absent_reason"] == "not_requested"


def test_metadata_does_not_mutate_the_caller_dict(tmp_path):
    """The retry path re-packs with a modified copy; mutating the original would corrupt it."""
    (tmp_path / "main.tf").write_text("")
    supplied = {"schema_version": 1, "code": {"repo_path": "infra"}}

    archive.pack(source_dir=str(tmp_path), metadata=supplied)

    assert supplied == {"schema_version": 1, "code": {"repo_path": "infra"}}
