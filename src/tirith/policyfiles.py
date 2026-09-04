"""
Finding policy files on disk, shared by `tirith lint` and `tirith fmt`.

A policy is a JSON object with at least one of the three top-level keys the engine reads --
`meta`, `evaluators`, `eval_expression`. Anything else that parses as JSON is not a policy and
is left alone, so pointing either command at a directory that also holds a `package.json` or a
plan document does not produce findings about files that were never policies.
"""

import json
import os
from typing import Any, List, NamedTuple, Optional, Sequence, Tuple

POLICY_KEYS = ("meta", "evaluators", "eval_expression")

# Directories never worth descending into. `.tirith` is not here on purpose: that is where
# policies conventionally live, and skipping dot-directories wholesale would skip it.
SKIPPED_DIRS = frozenset({".git", ".terraform", "node_modules", "__pycache__", ".venv", "venv"})

DEFAULT_POLICY_DIR = os.path.join(".tirith", "policies")


class PolicyFile(NamedTuple):
    path: str
    # Parsed document, or None when `error` is set.
    document: Any
    # Why the file could not be read as JSON, else None.
    error: Optional[str]
    # Original text, kept so `fmt` can tell whether rewriting would change anything.
    text: str


def looks_like_policy(document: Any) -> bool:
    return isinstance(document, dict) and any(key in document for key in POLICY_KEYS)


def read_policy_file(path: str) -> PolicyFile:
    """Read one file. A JSON error is reported on the file, not raised: the caller lists it."""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        return PolicyFile(path, None, f"cannot read: {e.strerror or e}", "")
    try:
        return PolicyFile(path, json.loads(text), None, text)
    except json.JSONDecodeError as e:
        return PolicyFile(path, None, f"not valid JSON: {e.msg} (line {e.lineno}, column {e.colno})", text)


def _walk_json_files(directory: str) -> List[str]:
    found = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = sorted(d for d in dirs if d not in SKIPPED_DIRS)
        for name in sorted(files):
            if name.endswith(".json"):
                found.append(os.path.join(root, name))
    return found


class Collected(NamedTuple):
    # Policy files, including ones that failed to parse (with `error` set): an unparseable
    # `.json` inside a policy directory is a defect to report, not a file to ignore.
    policies: List[PolicyFile]
    # Files named on the command line that parsed but are not policies. Reported by name, so a
    # typo'd path to a plan document does not read as a clean run.
    skipped: List[str]
    # JSON files met while walking a directory that are not policies -- input documents beside
    # their policies, usually. Counted, not listed: they are expected there.
    ignored: int
    # Paths that do not exist.
    missing: List[str]


def collect(paths: Sequence[str]) -> Collected:
    """
    Resolve command-line paths to policy files.

    :param paths: Files or directories. Empty means `.tirith/policies` if it exists, else `.`.
    """
    if not paths:
        paths = [DEFAULT_POLICY_DIR] if os.path.isdir(DEFAULT_POLICY_DIR) else ["."]

    policies: List[PolicyFile] = []
    skipped: List[str] = []
    ignored = 0
    missing: List[str] = []
    seen = set()

    for path in paths:
        if os.path.isdir(path):
            candidates = _walk_json_files(path)
            explicit = False
        elif os.path.isfile(path):
            candidates = [path]
            explicit = True
        else:
            missing.append(path)
            continue

        for candidate in candidates:
            key = os.path.abspath(candidate)
            if key in seen:
                continue
            seen.add(key)
            policy_file = read_policy_file(candidate)
            if policy_file.error is not None:
                policies.append(policy_file)
            elif looks_like_policy(policy_file.document):
                policies.append(policy_file)
            elif explicit:
                skipped.append(candidate)
            else:
                ignored += 1

    return Collected(policies, skipped, ignored, missing)
