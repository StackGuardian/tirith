#!/usr/bin/env python3
"""
Build src/data/contributors.js: everyone who has committed to Tirith, on any branch.

Why this is not just the contributors API. That endpoint only counts commits reachable from the
default branch, so anyone whose work lives on a branch that has not merged is invisible to it.
Running it against this repository returns 18 entries and misses one real person. A page that
thanks the community and then leaves a contributor off is worse than not having the page.

So the list is built from both ends:

  1. `GET /repos/:owner/:repo/contributors` for logins, avatars and commit counts.
  2. `git log --all` for every author across every ref, each resolved to a GitHub login. A
     `<id>+<login>@users.noreply.github.com` address carries the login directly; anything else is
     resolved by asking the API who authored one of that address's commits.

Both are needed. Step 2 alone cannot give a commit count or an avatar; step 1 alone cannot see a
branch. Identities are keyed on the numeric GitHub id, not the login, because a rename changes the
login and would otherwise list one person twice: two of the authors here have renamed, and both
were caught this way.

Avatar URLs are built from the numeric id for the same reason. `github.com/<login>.png` breaks the
moment someone renames; `avatars.githubusercontent.com/u/<id>` does not.

Requires network access. Unauthenticated GitHub allows 60 requests an hour, which is enough for
this repository; set GITHUB_TOKEN to raise it if that ever stops being true.

    python3 documentation/scripts/generate-contributors.py

The output is committed, so a build never needs the network and a fork gets the list for free.
Re-run it when someone new lands a commit.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
OUT = HERE.parent / "src" / "data" / "contributors.js"

OWNER_REPO = "StackGuardian/tirith"
API = f"https://api.github.com/repos/{OWNER_REPO}"

# Machine accounts. They commit, but the page is about people.
BOTS = {"dependabot[bot]", "dependabot-preview[bot]", "github-actions[bot]", "travis-ci"}

NOREPLY_WITH_ID = re.compile(r"^(\d+)\+([A-Za-z0-9-]+)@users\.noreply\.github\.com$")
NOREPLY_BARE = re.compile(r"^([A-Za-z0-9-]+)@users\.noreply\.github\.com$")


def api_get(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print("error: GitHub rate limit reached. Set GITHUB_TOKEN and retry.", file=sys.stderr)
            raise SystemExit(1)
        return None
    except urllib.error.URLError:
        return None


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False).stdout


def all_ref_authors() -> dict[str, str]:
    """Every distinct author email across every ref, mapped to the name it last used."""
    out: dict[str, str] = {}
    for line in git("log", "--all", "--format=%aE|%aN").splitlines():
        email, _, name = line.partition("|")
        if email.strip():
            out[email.strip().lower()] = name.strip()
    return out


def resolve_login(email: str) -> str | None:
    """The GitHub login behind a commit author address, or None if it cannot be resolved."""
    m = NOREPLY_WITH_ID.match(email) or NOREPLY_BARE.match(email)
    if m:
        return m.group(2) if m.lastindex == 2 else m.group(1)
    sha = git("log", "--all", "--format=%H", f"--author={email}", "-1").strip()
    if not sha:
        return None
    commit = api_get(f"{API}/commits/{sha}")
    author = (commit or {}).get("author")
    return author.get("login") if author else None


def main() -> int:
    contributors = api_get(f"{API}/contributors?per_page=100")
    if contributors is None:
        print("error: could not reach the GitHub API.", file=sys.stderr)
        return 1

    # Keyed on numeric id so a rename cannot produce two entries for one person.
    people: dict[int, dict] = {}
    for c in contributors:
        if c["login"].lower() in BOTS or c.get("type") == "Bot":
            continue
        people[c["id"]] = {
            "login": c["login"],
            "id": c["id"],
            "commits": c["contributions"],
            "branchOnly": False,
        }

    known_logins = {p["login"].lower() for p in people.values()}
    for email in sorted(all_ref_authors()):
        login = resolve_login(email)
        if not login or login.lower() in known_logins or login.lower() in BOTS:
            continue
        user = api_get(f"https://api.github.com/users/{login}")
        if not user or user.get("type") == "Bot":
            continue
        if user["id"] in people:  # a rename of somebody already listed
            continue
        commits = len(git("log", "--all", "--format=%H", f"--author={email}").splitlines())
        people[user["id"]] = {
            "login": user["login"],
            "id": user["id"],
            "commits": commits,
            "branchOnly": True,
        }
        known_logins.add(login.lower())
        time.sleep(0.4)

    ordered = sorted(people.values(), key=lambda p: (-p["commits"], p["login"].lower()))

    header = f"""/**
 * GENERATED FILE. Do not edit.
 *
 * Everyone who has committed to Tirith, on any branch. Regenerate with
 * documentation/scripts/generate-contributors.py, which explains how the list is built and
 * why the contributors API alone is not enough.
 *
 * Bots are excluded. `branchOnly` marks someone whose work has not reached the default
 * branch, and who the GitHub contributors API therefore does not list at all.
 *
 * Avatar URLs are keyed on the numeric GitHub id rather than the login, so a rename does not
 * break the image.
 */

export const CONTRIBUTOR_COUNT = {len(ordered)};

export const CONTRIBUTORS = [
"""
    rows = "".join(
        "  {{login: {login!r}, id: {id}, commits: {commits}{extra}}},\n".format(
            login=p["login"],
            id=p["id"],
            commits=p["commits"],
            extra=", branchOnly: true" if p["branchOnly"] else "",
        ).replace("'", '"')
        for p in ordered
    )
    OUT.write_text(header + rows + "];\n", encoding="utf-8")

    branch_only = [p["login"] for p in ordered if p["branchOnly"]]
    print(f"wrote {OUT.relative_to(HERE.parent)}: {len(ordered)} people")
    print(f"  branch-only, missed by the contributors API: {', '.join(branch_only) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
