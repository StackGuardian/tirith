"""Build a bundled policy pack from a tirith-policy-corpus checkout.

The corpus translates upstream checks into tirith policy documents and grades them into nested
evidence tiers (`verified` > `exact` > `confirmed`). This turns one of those tiers into a pack
under `src/tirith/packs/`, which is what `tirith --pack <name>` runs.

Two things happen on the way, and both are the point of having a tool rather than a copy:

1.  RENAMING. Shipped checks carry StackGuardian identifiers and nothing else -- no upstream
    check ids, no upstream project names, in the id, the filename, the tags or the prose. The
    mapping back to upstream stays in the corpus, in `pack_ids.json`, which is also what makes
    the ids stable: an id is allocated once for a policy and reused on every later sync, so
    re-running this with a wider tier appends and never renumbers.

2.  VERIFICATION. Nothing is written until every output has been re-read and checked for a
    leaked upstream name. A rename that half-works is worse than one that fails loudly.

Usage:
    python3 tools/sync_pack.py --corpus ../tirith-policy-corpus --tier confirmed \
        --pack-name terraform-baseline --description "..." [--fixtures-from DIR]

Tier selection is delegated to the corpus's own `tools/working_set.py`, so this tool never
has to restate what "confirmed" means.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKS_DIR = os.path.join(ROOT, "src", "tirith", "packs")
FIXTURES_DIR = os.path.join(ROOT, "tests", "packs", "fixtures")

# Data the corpus owns because it references upstream: the frozen id registry, and the prose
# rewrites for evaluator descriptions whose original text explains itself by naming the tool it
# was translated from. Keyed by "<batch>::<policy_key>" -- the join key the corpus uses
# everywhere, because upstream ids recur across frameworks and are not unique on their own.
ID_REGISTRY = "pack_ids.json"
OVERRIDES = "pack_overrides.json"

ID_FORMAT = "SG_TF_{:04d}"
ID_PATTERN = re.compile(r"^SG_TF_\d{4}$")

# Names that must not reach a shipped file. Checked case-insensitively over the whole document,
# including keys, after every rewrite. Kept explicit rather than clever: a missed name ships.
FORBIDDEN = (
    "checkov",
    "bridgecrew",
    "ckv",
    "trivy",
    "aquasecurity",
    "aqua security",
    "steampipe",
    "powerpipe",
    "turbot",
    "cfn-guard",
    "cfn_guard",
    "guard-rules-registry",
    "kics",
    "tfsec",
    "terrascan",
    "prowler",
    "regula",
    "conftest",
    "cloud custodian",
    "openssf",
    "scorecard",
    "snyk",
    "prisma",
    "wiz.io",
    # Not names, but upstream's API vocabulary, which reads as a translation artefact and points
    # at one particular scanner just as plainly as its name would.
    "missing_block_result",
    "missing_attribute_result",
    "any_value",
    "baseresourcevaluecheck",
    "jsonpath_not_exists",
    "card rule",
    "upstream",
)

# Terraform resource-type prefix -> the cloud tag. Anything unlisted keeps its own prefix, so a
# new provider shows up as itself rather than silently vanishing.
CLOUD_BY_PREFIX = {
    "aws": "aws",
    "azurerm": "azure",
    "azuread": "azure",
    "google": "gcp",
    "kubernetes": "kubernetes",
    "alicloud": "alicloud",
    "oci": "oci",
    "tencentcloud": "tencentcloud",
    "yandex": "yandex",
    "digitalocean": "digitalocean",
    "linode": "linode",
    "panos": "panos",
}

# Tags that say nothing a reader cannot already see: the provider is in `required_provider`.
DROPPED_TAGS = {"terraform", "json", "kubernetes_manifest"}


# --------------------------------------------------------------------------------------- corpus


def corpus_records(corpus: str) -> Dict[str, Dict]:
    """Every translated record, keyed by its `out_path`."""
    rows: Dict[str, Dict] = {}
    for pattern in ("records_*.jsonl", os.path.join("records2", "*.jsonl")):
        for path in sorted(glob.glob(os.path.join(corpus, pattern))):
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    if row.get("status") == "translated" and row.get("out_path"):
                        rows[row["out_path"]] = row
    return rows


def tier_paths(corpus: str, tier: str) -> List[str]:
    """Delegate tier selection to the corpus, which is where the standard is defined."""
    out = subprocess.run(
        [sys.executable, os.path.join("tools", "working_set.py"), "--tier", tier, "--list"],
        cwd=corpus,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def corpus_commit(corpus: str) -> str:
    out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=corpus, capture_output=True, text=True, check=True)
    return out.stdout.strip()


def load_json(path: str, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------------------------ rewriting


def join_key(record: Dict) -> str:
    """`(batch, policy_key)`, not policy_key alone: upstream ids recur across frameworks."""
    return f"{record.get('batch', '')}::{record['policy_key']}"


def allocate_ids(registry: Dict, keys: List[str]) -> Dict:
    """Give every unseen key the next id. Never reassigns one that already exists."""
    ids = registry.setdefault("ids", {})
    next_id = registry.get("next", 1)
    for key in keys:
        if key not in ids:
            ids[key] = ID_FORMAT.format(next_id)
            next_id += 1
    registry["scheme"] = ID_FORMAT
    registry["next"] = next_id
    return registry


def _first_provider_args(policy: Dict) -> Dict:
    for evaluator in policy.get("evaluators", []):
        args = evaluator.get("provider_args") or {}
        if args:
            return args
    return {}


def slug_for(policy: Dict) -> str:
    """
    A readable filename half, from what the policy actually reads.

    `aws_s3_bucket` + `versioning.*.enabled` -> `aws_s3_bucket_versioning_enabled`. Wildcards and
    list indices carry no meaning in a name, and a repeated word (the attribute restating the
    resource) is dropped, so the result reads like a sentence rather than a path.
    """
    args = _first_provider_args(policy)
    parts = [args.get("terraform_resource_type") or args.get("kubernetes_kind") or ""]
    parts.append(
        args.get("terraform_resource_attribute")
        or args.get("attribute_path")
        or args.get("key_path")
        or args.get("referenced_by")
        or args.get("references_to")
        or args.get("operation_type")
        or ""
    )

    words: List[str] = []
    for part in parts:
        for token in re.split(r"[^A-Za-z0-9]+", str(part)):
            token = token.lower()
            if not token or token.isdigit() or token == "":
                continue
            if token in words:
                continue
            words.append(token)

    slug = "_".join(words) or "policy"
    return slug[:70].rstrip("_")


def rewrite_tags(policy: Dict) -> List[str]:
    """Lowercase the upstream taxonomy, drop what the provider already says, add the cloud."""
    tags = []
    for tag in policy.get("meta", {}).get("tags", []) or []:
        normalised = str(tag).strip().lower()
        if not normalised or normalised in DROPPED_TAGS or normalised in tags:
            continue
        tags.append(normalised)

    resource_type = _first_provider_args(policy).get("terraform_resource_type") or ""
    prefix = resource_type.split("_")[0]
    cloud = CLOUD_BY_PREFIX.get(prefix)
    if cloud:
        cloud_tag = f"cloud:{cloud}"
        if cloud_tag not in tags:
            tags.insert(0, cloud_tag)
    return tags


def apply_overrides(policy: Dict, override: Dict) -> None:
    """Replace evaluator descriptions the corpus has supplied clean text for."""
    replacements = (override or {}).get("evaluator_descriptions") or {}
    unused = set(replacements)
    for evaluator in policy.get("evaluators", []):
        if evaluator.get("id") in replacements:
            evaluator["description"] = replacements[evaluator["id"]]
            unused.discard(evaluator["id"])
    if unused:
        raise SystemExit(f"override names evaluator(s) that do not exist: {', '.join(sorted(unused))}")


def forbidden_in(text: str) -> List[str]:
    lowered = text.lower()
    # `ckv` is matched on a word boundary; the others are distinctive enough to match anywhere.
    hits = [name for name in FORBIDDEN if name != "ckv" and name in lowered]
    if re.search(r"\bckv\b|\bckv[0-9]*_", lowered):
        hits.append("ckv")
    return hits


# ----------------------------------------------------------------------------------------- main


def build(corpus: str, tier: str, pack_name: str, description: str, fixtures_dir: Optional[str]) -> int:
    records = corpus_records(corpus)
    paths = tier_paths(corpus, tier)
    if not paths:
        raise SystemExit(f"tier '{tier}' selected no policies")

    registry_path = os.path.join(corpus, ID_REGISTRY)
    registry = load_json(registry_path, {})
    # Keys beginning with "_" are commentary in the overrides file, not policies.
    overrides = {
        key: value for key, value in load_json(os.path.join(corpus, OVERRIDES), {}).items() if not key.startswith("_")
    }

    selected: List[Tuple[str, Dict]] = []
    for rel in paths:
        record = records.get(rel)
        if record is None:
            raise SystemExit(f"no translated record for {rel}")
        selected.append((rel, record))

    keys = sorted(join_key(record) for _rel, record in selected)
    registry = allocate_ids(registry, keys)

    pack_dir = os.path.join(PACKS_DIR, pack_name)
    policies_dir = os.path.join(pack_dir, "policies")
    shutil.rmtree(pack_dir, ignore_errors=True)
    os.makedirs(policies_dir)

    manifest_policies = []
    leaked: List[str] = []
    used_overrides = set()

    for rel, record in sorted(selected, key=lambda item: registry["ids"][join_key(item[1])]):
        key = join_key(record)
        policy_id = registry["ids"][key]
        with open(os.path.join(corpus, rel), encoding="utf-8") as fh:
            policy = json.load(fh)

        if key in overrides:
            apply_overrides(policy, overrides[key])
            used_overrides.add(key)

        policy["meta"]["id"] = policy_id
        policy["meta"]["tags"] = rewrite_tags(policy)

        filename = f"{policy_id}_{slug_for(policy)}.json"
        rendered = json.dumps(policy, indent=2, ensure_ascii=False) + "\n"

        hits = forbidden_in(rendered) + forbidden_in(filename)
        if hits:
            leaked.append(f"{rel} -> {filename}: {', '.join(sorted(set(hits)))}")
            continue

        with open(os.path.join(policies_dir, filename), "w", encoding="utf-8") as fh:
            fh.write(rendered)

        manifest_policies.append(
            {
                "id": policy_id,
                "path": f"policies/{filename}",
                "name": policy["meta"].get("name", ""),
                "fidelity": record.get("fidelity", "approximate"),
                "required_provider": policy["meta"].get("required_provider", ""),
                "tags": policy["meta"]["tags"],
            }
        )

        if fixtures_dir:
            stem = os.path.relpath(rel, "policies")[:-5].replace(os.sep, "__")
            for kind in ("compliant", "violating"):
                src = os.path.join(fixtures_dir, f"{stem}.{kind}.json")
                if os.path.exists(src):
                    os.makedirs(FIXTURES_DIR, exist_ok=True)
                    shutil.copy(src, os.path.join(FIXTURES_DIR, f"{policy_id}.{kind}.json"))

    if leaked:
        shutil.rmtree(pack_dir, ignore_errors=True)
        print("refusing to write the pack -- upstream names survived the rename:", file=sys.stderr)
        for line in leaked:
            print(f"  {line}", file=sys.stderr)
        return 1

    stale = set(overrides) - used_overrides
    if stale:
        print(f"warning: {len(stale)} override(s) matched no selected policy", file=sys.stderr)

    manifest = {
        "name": pack_name,
        "description": description,
        "tier": tier,
        "source": {"repo": "StackGuardian/tirith-policy-corpus", "commit": corpus_commit(corpus)},
        "required_providers": sorted({p["required_provider"] for p in manifest_policies}),
        "count": len(manifest_policies),
        "policies": manifest_policies,
    }
    with open(os.path.join(pack_dir, "pack.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    with open(registry_path, "w", encoding="utf-8") as fh:
        json.dump(registry, fh, indent=2)
        fh.write("\n")

    print(f"wrote {len(manifest_policies)} policies to {os.path.relpath(pack_dir, ROOT)}")
    print(f"registry now holds {len(registry['ids'])} ids ({os.path.relpath(registry_path)})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True, help="path to a tirith-policy-corpus checkout")
    parser.add_argument("--tier", default="confirmed", choices=("verified", "exact", "confirmed"))
    parser.add_argument("--pack-name", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument(
        "--fixtures-from",
        metavar="DIR",
        help=(
            "copy each policy's compliant/violating fixtures from DIR into tests/packs/fixtures. "
            "The corpus does not commit fixtures/generated, so this has to be pointed at a "
            "checkout that has actually generated them."
        ),
    )
    args = parser.parse_args()
    return build(
        os.path.abspath(args.corpus),
        args.tier,
        args.pack_name,
        args.description,
        os.path.abspath(args.fixtures_from) if args.fixtures_from else None,
    )


if __name__ == "__main__":
    raise SystemExit(main())
