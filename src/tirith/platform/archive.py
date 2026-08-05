"""
Build the gzipped tar that carries a run's inputs to StackGuardian.

The archive is what the run controller unpacks in place of a VCS checkout, so it holds both the
terraform source and the documents to evaluate, at the fixed names the step looks for:

    plan.json       terraform plan JSON     -- the primary policy input
    tfstate.json      terraform state JSON
    infracost.json  cost breakdown

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
import tarfile

# Fixed names the tirith-check step looks for at the archive root.
PLAN_DOCUMENT = "plan.json"
STATE_DOCUMENT = "tfstate.json"
INFRACOST_DOCUMENT = "infracost.json"

# These names are ALWAYS written by pack(), never copied from the source tree -- whether or not a
# masked document was supplied for them. A file called tfstate.json in the working directory is raw,
# unmasked state; see the note in pack().
RESERVED_DOCUMENTS = frozenset((PLAN_DOCUMENT, STATE_DOCUMENT, INFRACOST_DOCUMENT))

# Always excluded, regardless of .gitignore.
#
# .terraform/       provider binaries and modules; hundreds of MB, and the runner does its own init
# .git/             full history, so anything ever committed would ship
# *.tfstate*        raw state -- unmasked by definition, including .backup files
# .terraform.lock.hcl is deliberately NOT excluded: it pins provider versions and is small.
DEFAULT_EXCLUDES = (
    ".git",
    ".terraform",
    "*.tfstate",
    "*.tfstate.*",
    "*.tfstate.backup",
    "__pycache__",
    "*.pyc",
    ".venv",
    "node_modules",
)

# Refuse to build anything larger than this. A runaway archive is nearly always an exclusion that
# did not fire, and failing loudly beats a five-minute upload that times out the run.
MAX_ARCHIVE_BYTES = 100 * 1024 * 1024


class ArchiveError(Exception):
    """The archive could not be built."""


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


def pack(source_dir, plan=None, state=None, infracost=None, extra_excludes=(), respect_gitignore=True):
    """
    Build the archive in memory and return its bytes.

    `plan`, `state` and `infracost` are already-redacted objects. They are serialized here and
    written at the archive root, overriding any same-named file in `source_dir` -- so a stale
    plan.json lying around cannot displace the masked one.

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
            manifest["files"], manifest["skipped"] = _add_tree(tar, source_dir, patterns, RESERVED_DOCUMENTS)
        for name, document in documents.items():
            _add_document(tar, name, document)

    archive = buffer.getvalue()
    if len(archive) > MAX_ARCHIVE_BYTES:
        raise ArchiveError(
            f"Archive is {len(archive) // (1024 * 1024)} MB, over the {MAX_ARCHIVE_BYTES // (1024 * 1024)} MB "
            "limit. This usually means a large directory was not excluded -- check for provider "
            "caches or build output, and pass extra excludes if needed."
        )

    manifest["bytes"] = len(archive)
    return archive, manifest


def _add_tree(tar, source_dir, patterns, reserved_names):
    """Walk `source_dir`, adding everything not excluded. Returns (added, skipped)."""
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
            else:
                kept_dirs.append(d)
        dirs[:] = kept_dirs

        for name in files:
            relative = os.path.join(relative_root, name) if relative_root else name
            if _is_excluded(relative, name, patterns):
                skipped += 1
                continue
            # The masked documents are written separately and must win.
            if relative in reserved_names:
                skipped += 1
                continue
            full = os.path.join(root, name)
            if os.path.islink(full):
                # A symlink out of the tree would either break on extraction or smuggle a file in.
                skipped += 1
                continue
            try:
                tar.add(full, arcname=relative)
                added += 1
            except OSError:
                skipped += 1

    return added, skipped


def _add_document(tar, name, document):
    """Serialize one document straight into the tar, never via a file on disk."""
    import json

    payload = document if isinstance(document, bytes) else json.dumps(document).encode("utf-8")
    info = tarfile.TarInfo(name=name)
    info.size = len(payload)
    info.mode = 0o644
    tar.addfile(info, io.BytesIO(payload))
