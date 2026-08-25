#!/usr/bin/env python3
"""
Find em dashes in anything that reaches a reader.

Written because two hand audits both missed real occurrences. The first looked only at
src/pages/*.js and missed the shared components; the second missed that a single dash inside a
component is multiplied by every item it renders -- two in the verdict renderer became 56 on the
policies page. Counting sources is not the same as counting what ships.

So this checks both: the authored files, and the built HTML. Run it after a build.

    python3 documentation/scripts/find-dashes.py            # source + build
    python3 documentation/scripts/find-dashes.py --built    # only what ships

Exits non-zero when the built site contains any, which makes it usable as a CI gate.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.dirname(HERE)

# En dashes are deliberately not flagged. In `1-10` or `lessons 1-3` an en dash is correct
# typography for a numeric range, not a stylistic tic, and replacing it with a hyphen would be
# a downgrade.
EM = "—"

SOURCE_DIRS = [("src", (".js", ".json", ".css")), ("docs", (".md",))]
SOURCE_FILES = ["docusaurus.config.js"]


def scan_source():
    rows = []
    for rel, exts in SOURCE_DIRS:
        root = os.path.join(DOCS, rel)
        for dirpath, _, names in os.walk(root):
            for name in sorted(names):
                if not name.endswith(exts):
                    continue
                path = os.path.join(dirpath, name)
                with open(path, encoding="utf-8") as handle:
                    for number, line in enumerate(handle, 1):
                        if EM in line:
                            rows.append((os.path.relpath(path, DOCS), number, line.strip()))
    for name in SOURCE_FILES:
        path = os.path.join(DOCS, name)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                if EM in line:
                    rows.append((name, number, line.strip()))
    return rows


def scan_built():
    """
    What a visitor receives. Counts per page, because one dash in a shared component shows up
    once per rendered item and that multiplication is the thing worth seeing.
    """
    build = os.path.join(DOCS, "build")
    if not os.path.isdir(build):
        return None
    counts = {}
    for dirpath, _, names in os.walk(build):
        for name in names:
            if name != "index.html":
                continue
            path = os.path.join(dirpath, name)
            with open(path, encoding="utf-8") as handle:
                found = handle.read().count(EM)
            if found:
                counts[os.path.relpath(path, build)] = found
    return counts


def main():
    only_built = "--built" in sys.argv

    if not only_built:
        rows = scan_source()
        by_file = {}
        for path, number, line in rows:
            by_file.setdefault(path, []).append((number, line))
        print(f"SOURCE: {len(rows)} em dash(es) in {len(by_file)} file(s)")
        for path in sorted(by_file):
            print(f"\n  {path}  ({len(by_file[path])})")
            for number, line in by_file[path][:40]:
                print(f"    {number:>5}  {line[:110]}")

    counts = scan_built()
    if counts is None:
        print("\nBUILT: no build/ directory; run `npm run build` first.")
        return 0
    total = sum(counts.values())
    print(f"\nBUILT: {total} em dash(es) reaching readers, across {len(counts)} page(s)")
    for path in sorted(counts, key=lambda p: -counts[p]):
        print(f"  {counts[path]:>5}  /{os.path.dirname(path) or ''}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
