#!/usr/bin/env python3
"""
Build static/llms-full.txt: every documentation page as one plain-text file.

Why this exists alongside llms.txt. llms.txt is a curated index, hand-written, and it is the
file to read when you want to know what Tirith is and which page answers a question.
llms-full.txt is the corpus: an agent that cannot fetch thirty URLs, or that wants the whole
reference in one request, gets it here. The two have different jobs and neither replaces the
other.

Generated rather than hand-maintained, because a hand-maintained copy of the documentation is
a second source of truth that goes stale silently, which is worse than not having one.

Run it after editing docs, before building:

    python3 documentation/scripts/generate-llms-full.py

The output is committed. It is small enough to diff, and committing it means the file exists
in a fork's build without anyone having to know this script is here.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCS = HERE.parent / "docs"
OUT = HERE.parent / "static" / "llms-full.txt"

SITE = "https://stackguardian.github.io/tirith"

# The reading order the sidebar uses. Alphabetical order would put the providers before
# getting started and the reference before the tutorial, which is the wrong shape for
# something read top to bottom.
ORDER = [
    "getting-started-with-tirith.md",
    "tirith-installation/quick-intallation.md",
    "tirith-installation/manual-installation.md",
    "tirith-installation/developer-mode-installation.md",
    "tirith-policies/tirith-create-first-policy.md",
    "tirith-policies/tirith-policy-structure.md",
    "tirith-policies/tirith-policy-reference.md",
    "tirith-policies/tirith-policy-conditions.md",
    "tirith-policies/tirith-policy-variables.md",
    "tirith-policies/tirith-policy-error-tolerance.md",
    "tirith-policies/tirith-policy-cookbook.md",
    "tirith-policies/tirith-policy-examples.md",
    "tirith-providers/overview.md",
    "tirith-providers/terraform-plan.md",
    "tirith-providers/json.md",
    "tirith-providers/kubernetes.md",
    "tirith-providers/infracost.md",
    "tirith-providers/sg-workflow.md",
    "tirith-reference/evaluators.md",
    "tirith-reference/eval-expressions.md",
    "tirith-usage/cli-reference.md",
    "tirith-usage/exit-codes.md",
    "tirith-usage/ci-integration.md",
    "tirith-usage/interactive-interface.md",
    "tirith-usage/editor-and-local.md",
    "tirith-usage/agent-skills.md",
    "tirith-usage/platform-check.md",
]


def front_matter(text: str) -> tuple[dict[str, str], str]:
    """Split YAML front matter off the body. Only the flat scalars are needed."""
    m = re.match(r"---\n(.*?)\n---\n?", text, re.S)
    if not m:
        return {}, text
    fields = dict(re.findall(r"^([a-z_]+): (.+)$", m.group(1), re.M))
    return fields, text[m.end() :]


def clean(body: str) -> str:
    """
    Flatten the MDX-only constructs into something a plain-text reader can follow.

    Docusaurus admonitions carry meaning: a `:::warning In development` block is the only
    thing marking an unshipped feature on some pages, so it becomes a labelled line rather
    than being dropped. Import statements and JSX tags carry none and go.
    """
    body = re.sub(r"^import .*$\n?", "", body, flags=re.M)
    body = re.sub(
        r"^:::(\w+)[ \t]*(.*)$",
        lambda m: f"[{m.group(1).upper()}]" + (f" {m.group(2)}" if m.group(2) else ""),
        body,
        flags=re.M,
    )
    body = re.sub(r"^:::$\n?", "", body, flags=re.M)
    body = re.sub(r"<br\s*/?>", "", body)
    # Docusaurus code-fence metadata (```yaml title="x") is not markdown.
    body = re.sub(r"^```(\w*)[ \t]+\S.*$", r"```\1", body, flags=re.M)
    return re.sub(r"\n{4,}", "\n\n\n", body).strip()


def main() -> int:
    missing = [p for p in ORDER if not (DOCS / p).is_file()]
    on_disk = {str(p.relative_to(DOCS)) for p in DOCS.rglob("*.md")}
    unlisted = sorted(on_disk - set(ORDER))

    # Fail loudly rather than silently shipping a partial corpus. A doc added without being
    # placed in ORDER is the failure this catches, and it is the likely one.
    if missing or unlisted:
        for p in missing:
            print(f"error: listed in ORDER but not on disk: {p}", file=sys.stderr)
        for p in unlisted:
            print(f"error: on disk but not listed in ORDER: {p}", file=sys.stderr)
        print("\nAdd it to ORDER in the position the sidebar uses.", file=sys.stderr)
        return 1

    parts = [
        "# Tirith: complete documentation",
        "",
        "Every documentation page of https://stackguardian.github.io/tirith/ in one file,",
        "in the order the sidebar presents them. Generated from the source markdown by",
        "documentation/scripts/generate-llms-full.py, so it cannot disagree with the site.",
        "",
        "For a short index instead, with the facts most answers get wrong, read",
        f"{SITE}/llms.txt",
        "",
    ]

    for rel in ORDER:
        fields, body = front_matter((DOCS / rel).read_text(encoding="utf-8"))
        slug = fields.get("slug") or fields.get("id") or ""
        url = f"{SITE}/docs/{rel.rsplit('/', 1)[0] + '/' if '/' in rel else ''}{slug}"
        parts += [
            "",
            "=" * 78,
            f"# {fields.get('title', rel)}",
            f"Source: {url}",
        ]
        if fields.get("description"):
            parts.append(f"Summary: {fields['description']}")
        parts += ["=" * 78, "", clean(body), ""]

    OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    kb = OUT.stat().st_size / 1024
    print(f"wrote {OUT.relative_to(HERE.parent)}: {len(ORDER)} pages, {kb:.0f} KB")

    # Each page again, on its own, as markdown beside the HTML route.
    #
    # An agent that wants one page should not have to fetch 152 KB or parse a rendered
    # document to get at it. The convention is the route plus `.md`, so
    # /docs/tirith-usage/exit-codes/ has /docs/tirith-usage/exit-codes.md next to it. No
    # collision: the route is a directory, this is a file beside it.
    md_root = HERE.parent / "static" / "docs"
    written = 0
    for rel in ORDER:
        fields, body = front_matter((DOCS / rel).read_text(encoding="utf-8"))
        slug = fields.get("slug") or fields.get("id") or ""
        folder = rel.rsplit("/", 1)[0] + "/" if "/" in rel else ""
        url = f"{SITE}/docs/{folder}{slug}"
        # Named for the route, not the source file: quick-intallation.md is a typo in the
        # filename that the slug already corrects, and the URL is what a reader has.
        dest = md_root / folder / (slug.rstrip("/") + ".md")
        dest.parent.mkdir(parents=True, exist_ok=True)
        head = [f"# {fields.get('title', slug)}", "", f"Source: {url}"]
        if fields.get("description"):
            head.append(f"Summary: {fields['description']}")
        dest.write_text("\n".join(head) + "\n\n" + clean(body) + "\n", encoding="utf-8")
        written += 1
    print(f"wrote {written} page files under static/docs/")

    # The same llms.txt, as a JS module, for the landing page's agent mode.
    #
    # The page renders this rather than a second brief written by hand, so there is one
    # source of truth and no way for the two to disagree. Emitted as a JSON string literal
    # rather than a template literal: llms.txt is full of backticks, and a template literal
    # would need every one escaped.
    llms = HERE.parent / "static" / "llms.txt"
    if llms.is_file():
        brief = HERE.parent / "src" / "data" / "agentBrief.js"
        brief.write_text(
            "/**\n"
            " * GENERATED FILE. Do not edit.\n"
            " *\n"
            " * The contents of static/llms.txt, for the landing page's agent mode. Edit\n"
            " * static/llms.txt and re-run documentation/scripts/generate-llms-full.py.\n"
            " */\n\n"
            "export const AGENT_BRIEF = " + json.dumps(llms.read_text(encoding="utf-8")) + ";\n",
            encoding="utf-8",
        )
        print(f"wrote {brief.relative_to(HERE.parent)}: {llms.stat().st_size / 1024:.1f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
