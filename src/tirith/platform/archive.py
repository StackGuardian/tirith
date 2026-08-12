"""
Build the gzipped tar that carries a run's inputs to StackGuardian.

The step unpacks this and reads the documents out of it, so the layout is a contract:

    plan.json       terraform plan JSON     -- the primary policy input
    tfstate.json    terraform state JSON
    infracost.json  cost breakdown
    metadata.json   what this bundle is: repository, commit, where the code belongs
    code/           the terraform source, if any was packed

**The documents stay at the root.** The step joins those three names onto the extraction directory and
treats absence as normal -- so moving one under a prefix would not raise, it would make every policy
report "unevaluated" and the run would look like it passed with warnings.

**`code/` is a prefix, not a directory member.** Nothing writes an explicit directory entry, so the
prefix exists in the tar only while at least one file carries it. `metadata.json` says so rather than
leaving a consumer to infer it from an absence.

Two things here are easy to get wrong and expensive to get wrong.

**The masked documents go in, never the originals.** `pack()` takes already-redacted objects and
serializes them itself; it never copies plan.json off disk. A caller that packed the source
directory *first* and masked afterwards would ship the plaintext file alongside the masked one. The
tests assert on the bytes inside the resulting tarball for this reason -- asserting on the dict
that was passed in would pass while the archive leaked.

**`.terraform/` must be excluded.** A provider cache is routinely hundreds of megabytes; including
it would make every run upload the AWS provider. `*.tfstate*` is excluded for the same reason as
the first point: an unmasked state file sitting in the working directory would otherwise travel
next to the masked copy.
"""

import fnmatch
import io
import os
import posixpath
import tarfile

# Fixed names the step looks for at the archive root.
PLAN_DOCUMENT = "plan.json"
STATE_DOCUMENT = "tfstate.json"
INFRACOST_DOCUMENT = "infracost.json"

# What this bundle is, for whatever reads it later. Written at the root beside the documents.
METADATA_DOCUMENT = "metadata.json"

# The source tree lives under here, so the root belongs to us alone.
CODE_PREFIX = "code"

# These names are ALWAYS written by pack(), never copied from the source tree -- whether or not a
# masked document was supplied for them.
#
# This is a LEAK guard, not a collision guard, and the distinction matters now that the source sits
# under `code/` where it cannot collide with anything. A file called tfstate.json in the working
# directory is raw, unmasked state by definition -- `terraform state pull > state.json` is the
# documented way to make one -- so packing it as `code/tfstate.json` would ship every attribute in
# plaintext next to the masked copy. Nothing about the prefix makes that safe; see the note in pack().
#
# metadata.json is here for a plainer reason: it is a thoroughly ordinary filename for a repository to
# contain, tar tolerates duplicate members, and extraction order would decide which one won.
RESERVED_DOCUMENTS = frozenset((PLAN_DOCUMENT, STATE_DOCUMENT, INFRACOST_DOCUMENT, METADATA_DOCUMENT))

# Always excluded, regardless of .gitignore.
#
# .terraform/       provider binaries and modules; hundreds of MB, and the runner does its own init
# .git/             full history, so anything ever committed would ship
# *.tfstate*        raw state -- unmasked by definition, including .backup files
# tfplan / *.tfplan the BINARY plan. It embeds the prior state, so it carries every attribute of
#                   every existing resource in plaintext -- strictly worse than a raw state file,
#                   and it matches none of the *.tfstate patterns. `--plan-file` reads it, converts
#                   it and masks the result in memory, which the source walk then undid by packing
#                   the original.
# .terraform.lock.hcl is deliberately NOT excluded: it pins provider versions and is small.
DEFAULT_EXCLUDES = (
    ".git",
    ".terraform",
    "*.tfstate",
    "*.tfstate.*",
    "tfplan",
    "*.tfplan",
    "*.tfplan.*",
    "__pycache__",
    "*.pyc",
    ".venv",
    "node_modules",
)

# Refuse to build anything larger than this. A runaway archive is nearly always an exclusion that
# did not fire, and failing loudly beats a five-minute upload that times out the run.
#
# Overridable, because the source tree is packed by default and the only other lever is dropping it
# entirely: a large monorepo that genuinely needs to ship its code has nowhere else to go. Raising it
# trades a clear error for a slow upload and more memory on the runner -- the whole archive is built
# in memory before this is checked -- so it is deliberately not a documented headline.
MAX_ARCHIVE_BYTES = 100 * 1024 * 1024

_override = os.environ.get("TIRITH_MAX_ARCHIVE_BYTES", "").strip()
if _override:
    try:
        MAX_ARCHIVE_BYTES = int(_override)
    except ValueError:
        # Not worth failing a run over; the default is a safe answer.
        pass


class ArchiveError(Exception):
    """The archive could not be built."""


def _human_bytes(count):
    """
    A size a person can read.

    Integer MB division reported anything under a megabyte as "0 MB", which is what the size limit
    message used to say -- and that message is now surfaced on a pull request, where "0 MB over the
    0 MB limit" tells the reader nothing.
    """
    for unit, size in (("MB", 1024 * 1024), ("KB", 1024)):
        if count >= size:
            return f"{count / size:.1f} {unit}"
    return f"{count} bytes"


def _load_gitignore_patterns(source_dir):
    """
    Read .gitignore into fnmatch patterns.

    Deliberately simple: leading `/` and trailing `/` are stripped, negations (`!`) are ignored.
    A full gitignore implementation is not worth it here -- DEFAULT_EXCLUDES covers the cases that
    actually matter, and .gitignore is a convenience on top.
    """
    path = os.path.join(source_dir, ".gitignore")
    patterns = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("!"):
                    continue
                patterns.append(line.strip("/"))
    except OSError:
        return []
    return patterns


def _is_excluded(relative_path, name, patterns):
    """Match a path against the exclusion patterns, by both basename and full relative path."""
    for pattern in patterns:
        if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(relative_path, pattern):
            return True
        # A directory pattern excludes everything beneath it.
        if relative_path.startswith(pattern + os.sep):
            return True
    return False


def pack(
    source_dir,
    plan=None,
    state=None,
    infracost=None,
    extra_excludes=(),
    respect_gitignore=True,
    document_sources=(),
    metadata=None,
):
    """
    Build the archive in memory and return its bytes.

    `plan`, `state` and `infracost` are already-redacted objects. They are serialized here and
    written at the archive root, overriding any same-named file in `source_dir` -- so a stale
    plan.json lying around cannot displace the masked one.

    `metadata` is the caller's half of `metadata.json`: what it intended. This function fills in the
    half only it can observe -- whether a tree was actually walked, under what prefix, and how many
    files went in or were skipped -- and writes the member last. The split is deliberate: a bundle
    that claims code but packed nothing is detectable only because the count is produced here rather
    than asserted by the caller.

    `document_sources` are the paths those objects were *read from*. They are excluded from the
    source walk, because the file on disk is the unmasked original: masking `tfplan.json` and then
    packing the source tree shipped the plaintext copy one filename away from the redacted one.
    Reserving only the three names this function writes was not enough -- the input is routinely
    called something else (`tfplan.json`, `state.json`, or the binary `tfplan`, which carries the
    prior state inside it).

    Returns (archive_bytes, manifest) where manifest lists what went in, for logging.
    """
    if source_dir and not os.path.isdir(source_dir):
        raise ArchiveError(f"Source directory does not exist: {source_dir}")

    patterns = list(DEFAULT_EXCLUDES) + list(extra_excludes)
    if respect_gitignore and source_dir:
        patterns += _load_gitignore_patterns(source_dir)

    documents = {}
    if plan is not None:
        documents[PLAN_DOCUMENT] = plan
    if state is not None:
        documents[STATE_DOCUMENT] = state
    if infracost is not None:
        documents[INFRACOST_DOCUMENT] = infracost

    buffer = io.BytesIO()
    manifest = {"documents": sorted(documents), "files": 0, "skipped": 0}

    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        if source_dir:
            # RESERVED_DOCUMENTS, not just the ones being written. A file named tfstate.json in the
            # working directory is unmasked by definition -- `terraform state pull > state.json` is
            # the documented way to produce one -- so packing it would ship every attribute in
            # plaintext beside the masked copy. If the caller wants it evaluated they pass
            # --state-path, which masks it first.
            #
            # Plus whatever the documents were actually read from, which is usually named something
            # else entirely.
            reserved = set(RESERVED_DOCUMENTS) | _relative_sources(source_dir, document_sources)
            manifest["files"], manifest["skipped"] = _add_tree(tar, source_dir, patterns, reserved)
        for name, document in documents.items():
            _add_document(tar, name, document)
        if metadata is not None:
            _add_document(tar, METADATA_DOCUMENT, _observed_metadata(metadata, source_dir, manifest))

    archive = buffer.getvalue()
    if len(archive) > MAX_ARCHIVE_BYTES:
        raise ArchiveError(
            f"Archive is {_human_bytes(len(archive))}, over the {_human_bytes(MAX_ARCHIVE_BYTES)} "
            "limit. This usually means a large directory was not excluded -- check for provider "
            "caches or build output, and pass extra excludes if needed."
        )

    manifest["bytes"] = len(archive)
    return archive, manifest


def _observed_metadata(metadata, source_dir, manifest):
    """
    Overlay what this module observed onto the caller's metadata, without mutating it.

    `code.present` is `files > 0`, not "a source directory was requested". Nothing writes an explicit
    directory member, so a tree where every file was excluded leaves no `code/` in the tar at all --
    and a consumer comparing the two must not find them disagreeing. `present` therefore means
    literally "there are members under the prefix".

    The caller's `code.absent_reason` survives when it has one (it knows *why* it asked for no source);
    a tree that was requested and vanished into the exclude list gets one from here, because the caller
    cannot know that happened.
    """
    code = dict(metadata.get("code") or {})
    files = manifest.get("files", 0)
    present = bool(source_dir) and files > 0

    code["present"] = present
    code["prefix"] = f"{CODE_PREFIX}/" if present else None
    code["files"] = files
    code["skipped"] = manifest.get("skipped", 0)
    if not present:
        code["repo_path"] = None
        code["repo_path_from"] = None
        if not code.get("absent_reason"):
            code["absent_reason"] = "empty_after_excludes" if source_dir else "not_requested"

    merged = dict(metadata)
    merged["code"] = code
    merged["documents"] = {
        "plan": PLAN_DOCUMENT if PLAN_DOCUMENT in manifest.get("documents", ()) else None,
        "state": STATE_DOCUMENT if STATE_DOCUMENT in manifest.get("documents", ()) else None,
        "infracost": INFRACOST_DOCUMENT if INFRACOST_DOCUMENT in manifest.get("documents", ()) else None,
    }
    return merged


def _add_tree(tar, source_dir, patterns, reserved_names, prefix=CODE_PREFIX):
    """
    Walk `source_dir`, adding everything not excluded under `prefix`. Returns (added, skipped).

    Member names are built with `posixpath`, not `os.path`: tar names are `/`-separated on every
    platform, and joining with the OS separator would emit backslashes on Windows -- extracting to
    literal one-segment filenames with backslashes in them.
    """
    added = 0
    skipped = 0

    for root, dirs, files in os.walk(source_dir):
        relative_root = os.path.relpath(root, source_dir)
        relative_root = "" if relative_root == "." else relative_root

        # Prune in place so os.walk does not descend into excluded directories at all -- the point
        # of excluding .terraform is not to read it.
        kept_dirs = []
        for d in dirs:
            relative = os.path.join(relative_root, d) if relative_root else d
            if _is_excluded(relative, d, patterns):
                skipped += 1
            elif os.path.islink(os.path.join(root, d)):
                # os.walk does not follow symlinked directories, so this one contributes nothing --
                # count it rather than letting a whole subtree disappear without appearing anywhere in
                # the manifest. Same reasoning as the file-level islink guard below.
                skipped += 1
            else:
                kept_dirs.append(d)
        dirs[:] = kept_dirs

        for name in files:
            relative = os.path.join(relative_root, name) if relative_root else name
            if _is_excluded(relative, name, patterns):
                skipped += 1
                continue
            # Reserved names are skipped on the path they have in the SOURCE tree, before the prefix
            # is applied. `code/tfstate.json` could not displace the masked root copy, but it would
            # still be unmasked state inside the bundle -- which is the actual reason for this skip.
            if relative in reserved_names:
                skipped += 1
                continue
            full = os.path.join(root, name)
            if os.path.islink(full):
                # A symlink out of the tree would either break on extraction or smuggle a file in.
                skipped += 1
                continue
            if not os.path.isfile(full):
                # Sockets, fifos and device nodes. `tar.add` does not raise for a type it cannot
                # classify -- it debug-logs "Unsupported type" and returns -- so counting the attempt
                # made `added` disagree with what the tar actually holds, and `code.present` could
                # then be true with nothing under the prefix at all.
                skipped += 1
                continue
            try:
                tar.add(full, arcname=posixpath.join(prefix, relative.replace(os.sep, "/")))
                added += 1
            except OSError:
                skipped += 1

    return added, skipped


def _relative_sources(source_dir, document_sources):
    """
    The document source paths, expressed the way _add_tree names members, for exclusion.

    Anything outside `source_dir` is dropped rather than kept as an unanchored basename: it cannot
    collide with a member name, and excluding a bare basename would silently drop an unrelated
    same-named file from the archive.
    """
    relative = set()
    try:
        root = os.path.realpath(source_dir)
    except OSError:
        return relative

    for path in document_sources or ():
        if not path:
            continue
        try:
            full = os.path.realpath(path)
            rel = os.path.relpath(full, root)
        except (OSError, ValueError):
            continue
        if rel != os.pardir and not rel.startswith(os.pardir + os.sep) and not os.path.isabs(rel):
            relative.add(rel)
    return relative


def _add_document(tar, name, document):
    """Serialize one document straight into the tar, never via a file on disk."""
    import json

    payload = document if isinstance(document, bytes) else json.dumps(document).encode("utf-8")
    info = tarfile.TarInfo(name=name)
    info.size = len(payload)
    info.mode = 0o644
    tar.addfile(info, io.BytesIO(payload))
