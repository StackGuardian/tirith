"""
The bundled packs are shipped content, so they are tested like code.

Three things are checked, and each has failed somewhere before:

  * the rename holds -- no upstream project name, check id or API vocabulary in a shipped file
  * every policy is structurally valid, using tirith's own validator rather than a second schema
  * every policy still *flips*: it passes its compliant fixture and fails its violating one

The third is the one that earns its keep. A pack is generated once and then sits still while the
engine moves underneath it, so an engine change that silently turns a check into a no-op would
otherwise be invisible: the pack would keep running and keep reporting green.

Fixtures live in tests/packs/fixtures and are deliberately not shipped in the wheel -- they are
how the pack is tested, not part of what it does.
"""

import json
import logging
import os
import re

import pytest

from tirith import packs
from tirith.core.core import start_policy_evaluation_from_dict
from tirith.tui.validate import check_policy

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")

ID_PATTERN = re.compile(r"^SG_TF_\d{4}$")

# Kept in step with tools/sync_pack.py's own denylist. Duplicated on purpose: the generator
# refusing to write a leak and the test refusing to ship one are two independent gates, and a
# shared constant would let one edit disable both.
FORBIDDEN = (
    "checkov",
    "bridgecrew",
    "trivy",
    "aquasecurity",
    "steampipe",
    "powerpipe",
    "turbot",
    "cfn-guard",
    "kics",
    "tfsec",
    "terrascan",
    "prowler",
    "openssf",
    "missing_block_result",
    "missing_attribute_result",
    "any_value",
    "baseresourcevaluecheck",
    "upstream",
)


def installed_packs():
    return packs.list_packs()


def all_policy_paths():
    found = []
    for pack in installed_packs():
        found += packs.pack_policy_paths(pack)
    return found


def test_at_least_one_pack_is_bundled():
    # If package_data or MANIFEST.in ever drops the pack, everything else here passes vacuously.
    assert installed_packs(), "no packs bundled -- check setup.py package_data and MANIFEST.in"


@pytest.mark.parametrize("pack", installed_packs(), ids=lambda p: p.name)
def test_manifest_matches_disk(pack):
    on_disk = {os.path.basename(path) for _name, path in packs.pack_policy_paths(pack)}
    declared = {os.path.basename(entry["path"]) for entry in pack.manifest["policies"]}
    assert declared == on_disk
    assert pack.manifest["count"] == len(on_disk)


@pytest.mark.parametrize("name,path", all_policy_paths(), ids=lambda value: os.path.basename(str(value)))
def test_policy_is_valid(name, path):
    with open(path) as f:
        policy = json.load(f)
    errors = [finding for finding in check_policy(policy) if finding.severity == "error"]
    assert not errors, f"{name}: {[str(finding) for finding in errors]}"


@pytest.mark.parametrize("name,path", all_policy_paths(), ids=lambda value: os.path.basename(str(value)))
def test_policy_id_is_a_stackguardian_id(name, path):
    with open(path) as f:
        policy = json.load(f)
    assert ID_PATTERN.match(policy["meta"]["id"]), policy["meta"]["id"]


def test_policy_ids_are_unique():
    seen = {}
    for name, path in all_policy_paths():
        with open(path) as f:
            policy_id = json.load(f)["meta"]["id"]
        assert policy_id not in seen, f"{name} reuses the id of {seen[policy_id]}"
        seen[policy_id] = name


@pytest.mark.parametrize("pack", installed_packs(), ids=lambda p: p.name)
def test_no_upstream_name_survives(pack):
    leaks = []
    for dirpath, _dirnames, filenames in os.walk(pack.path):
        for filename in filenames:
            full = os.path.join(dirpath, filename)
            with open(full, encoding="utf-8") as f:
                haystack = (filename + "\n" + f.read()).lower()
            hits = [name for name in FORBIDDEN if name in haystack]
            if re.search(r"\bckv\b|\bckv[0-9]*_", haystack):
                hits.append("ckv")
            if hits:
                leaks.append(f"{filename}: {sorted(set(hits))}")
    assert not leaks, leaks


@pytest.mark.parametrize("name,path", all_policy_paths(), ids=lambda value: os.path.basename(str(value)))
def test_policy_verdict_flips(name, path):
    with open(path) as f:
        policy = json.load(f)
    policy_id = policy["meta"]["id"]

    compliant = os.path.join(FIXTURES_DIR, f"{policy_id}.compliant.json")
    violating = os.path.join(FIXTURES_DIR, f"{policy_id}.violating.json")
    if not (os.path.exists(compliant) and os.path.exists(violating)):
        pytest.skip(f"no fixtures for {policy_id}")

    # The engine logs a warning for every tolerated provider miss, and a flip test drives
    # thousands of them.
    logging.disable(logging.CRITICAL)
    try:
        with open(compliant) as f:
            good = start_policy_evaluation_from_dict(policy, json.load(f))
        with open(violating) as f:
            bad = start_policy_evaluation_from_dict(policy, json.load(f))
    finally:
        logging.disable(logging.NOTSET)

    assert good.get("final_result") is True, f"{name} did not pass its compliant document"
    assert bad.get("final_result") is False, f"{name} did not fail its violating document"
