"""
The worked examples the playground opens with.

A playground with an empty buffer asks the user to already know the policy format, which is
the thing they came to learn. So it ships with runnable policy/input pairs -- pick one, see it
evaluate, edit it and watch the verdict move.

The examples live in `examples/` beside this module rather than being read out of `tests/`.
Reusing the test fixtures was tempting since there are ~30 of them, but tests/ is not shipped
in the wheel (MANIFEST.in packages `src/*.json`, and the test tree only reaches an sdist), so
an installed `pip install tirith-iac-governance[tui]` would have found an empty playground. They are also
written to demonstrate the engine, not to teach it: several exist precisely because they are
malformed, and `policy.json` uses a `&` the engine rejects outright.

Each example is a directory holding `policy.json`, `input.json` and `about.md`, discovered at
import rather than listed here, so adding one is a matter of adding the directory.
"""

import json
import os
from typing import Any, Dict, List, NamedTuple, Optional

EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "examples")

POLICY_FILENAME = "policy.json"
INPUT_FILENAME = "input.json"
ABOUT_FILENAME = "about.md"


class Example(NamedTuple):
    """One runnable policy/input pair."""

    # Directory name, used as a stable id. The numeric prefix orders the list from simplest to
    # most involved and is stripped from the display title.
    key: str
    title: str
    summary: str
    about: str
    policy: Dict[str, Any]
    input_document: Any
    provider: str

    @property
    def policy_json(self) -> str:
        return json.dumps(self.policy, indent=2)

    @property
    def input_json(self) -> str:
        return json.dumps(self.input_document, indent=2)


def _title_from_key(key: str) -> str:
    """`02-cost-ceiling` -> `Cost ceiling`."""
    without_prefix = key.split("-", 1)[1] if "-" in key and key.split("-", 1)[0].isdigit() else key
    return without_prefix.replace("-", " ").capitalize()


def _read_about(directory: str) -> str:
    path = os.path.join(directory, ABOUT_FILENAME)
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def _load_one(key: str) -> Optional[Example]:
    directory = os.path.join(EXAMPLES_DIR, key)
    policy_path = os.path.join(directory, POLICY_FILENAME)
    input_path = os.path.join(directory, INPUT_FILENAME)
    if not (os.path.exists(policy_path) and os.path.exists(input_path)):
        return None

    with open(policy_path, encoding="utf-8") as f:
        policy = json.load(f)
    with open(input_path, encoding="utf-8") as f:
        input_document = json.load(f)

    about = _read_about(directory)
    # The first line of about.md is the one-line summary shown in the picker; the rest is the
    # detail pane. Keeping both in one file means an example is a directory, with nothing to
    # register anywhere else.
    summary = about.splitlines()[0].strip() if about else ""

    return Example(
        key=key,
        title=_title_from_key(key),
        summary=summary,
        about=about,
        policy=policy,
        input_document=input_document,
        provider=policy.get("meta", {}).get("required_provider", ""),
    )


def load_examples() -> List[Example]:
    """
    Every bundled example, ordered by directory name.

    Returns an empty list rather than raising when the directory is missing, so a partial
    install degrades to a playground with no examples instead of an unusable one.
    """
    if not os.path.isdir(EXAMPLES_DIR):
        return []

    found: List[Example] = []
    for key in sorted(os.listdir(EXAMPLES_DIR)):
        if key.startswith(".") or not os.path.isdir(os.path.join(EXAMPLES_DIR, key)):
            continue
        example = _load_one(key)
        if example is not None:
            found.append(example)
    return found


def example_by_key(key: str) -> Optional[Example]:
    for example in load_examples():
        if example.key == key:
            return example
    return None
