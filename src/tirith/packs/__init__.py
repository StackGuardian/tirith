"""
Predefined policy packs that ship inside tirith.

A pack is a directory holding a `pack.json` manifest and a `policies/` directory of ordinary
tirith policy documents. Nothing about a packed policy is special -- each one runs through
`start_policy_evaluation_from_dict` exactly as a file passed with `-policy-path` does. The pack
is only a name for a set, so that `--pack terraform-baseline` is a thing a user can type.

Located by walking up from this file rather than through `importlib.resources`: `files()` is
3.9+ and setup.py declares `python_requires=">=3.8"`. `tui/examples.py` locates its bundled
examples the same way, for the same reason.

Every lookup degrades rather than raising when the directory is missing: a partial install
should list no packs, not crash on startup. `setup.py`'s `package_data` and `MANIFEST.in` are
what actually put the files in the distribution, and both have been wrong before.
"""

import json
import os
from typing import Dict, List, NamedTuple, Optional, Tuple

PACKS_DIR = os.path.dirname(os.path.abspath(__file__))

MANIFEST_NAME = "pack.json"
POLICIES_DIRNAME = "policies"


class Pack(NamedTuple):
    """A bundled pack, as read from its manifest."""

    name: str
    description: str
    path: str
    manifest: Dict

    @property
    def count(self) -> int:
        """How many policies the manifest claims. `policy_paths` is the authority on disk."""
        return self.manifest.get("count", len(self.manifest.get("policies", [])))


def _read_manifest(pack_dir: str) -> Optional[Dict]:
    manifest_path = os.path.join(pack_dir, MANIFEST_NAME)
    if not os.path.isfile(manifest_path):
        return None
    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, ValueError):
        return None
    return manifest if isinstance(manifest, dict) else None


def _load_one(name: str) -> Optional[Pack]:
    pack_dir = os.path.join(PACKS_DIR, name)
    manifest = _read_manifest(pack_dir)
    if manifest is None:
        return None
    return Pack(
        name=manifest.get("name", name),
        description=manifest.get("description", ""),
        path=pack_dir,
        manifest=manifest,
    )


def list_packs() -> List[Pack]:
    """Every bundled pack, ordered by directory name. Empty when none are installed."""
    if not os.path.isdir(PACKS_DIR):
        return []

    found = []
    for key in sorted(os.listdir(PACKS_DIR)):
        if key.startswith(".") or key.startswith("__"):
            continue
        if not os.path.isdir(os.path.join(PACKS_DIR, key)):
            continue
        pack = _load_one(key)
        if pack is not None:
            found.append(pack)
    return found


def resolve_pack(name: str) -> Optional[Pack]:
    """The pack called `name`, or None if no such pack is installed."""
    # Matched on the directory name and on the manifest's own `name`, which are expected to
    # agree; the manifest wins if they ever do not, because that is what --list-packs prints.
    direct = _load_one(name)
    if direct is not None:
        return direct
    for pack in list_packs():
        if pack.name == name:
            return pack
    return None


def pack_policy_paths(pack: Pack) -> List[Tuple[str, str]]:
    """
    (name, path) pairs for every policy in `pack`, ordered by filename.

    Read from disk rather than from the manifest's `policies` list: the files are what runs, and
    a manifest that has drifted from them should not silently skip a check. `tests/packs`
    asserts the two agree.
    """
    policies_dir = os.path.join(pack.path, POLICIES_DIRNAME)
    if not os.path.isdir(policies_dir):
        return []
    return [
        (f"{pack.name}/{fname}", os.path.join(policies_dir, fname))
        for fname in sorted(os.listdir(policies_dir))
        if fname.endswith(".json")
    ]
