#!/usr/bin/env sh
#
# Install the Tirith policy skill for a coding agent.
#
#   curl -fsSL https://stackguardian.github.io/tirith/skill.sh | sh
#
# Read this file before you run it. It is served over HTTPS from the documentation site and
# its source is documentation/static/skill.sh in StackGuardian/tirith, so the version you
# are about to pipe into a shell is the version you can read in the repository.
#
# What it does: downloads two skills into .claude/skills/ -- tirith-policies (eleven markdown
# files plus a worked example) and tirith-migrate (Sentinel-to-Tirith translation, with its
# classified corpus and five worked examples) -- and, with --cursor, one rule file into
# .cursor/rules/. It creates directories, writes those files, and nothing else. No package is installed, no PATH is changed, nothing is executed
# after download, and it never touches a file it did not create.
#
# Flags:
#   --global   install into ~/.claude/skills/ instead of ./.claude/skills/
#   --cursor   also install the Cursor rule into .cursor/rules/
#   --ref REF  install from a branch or tag instead of main
#
# POSIX sh on purpose: it runs under dash, ash and busybox, which is what a slim CI image
# gives you.

set -eu

REPO="StackGuardian/tirith"
REF="main"
PACK=".claude/skills/tirith-policies"
DEST="."
CURSOR=0
MIGRATE_PACK=".claude/skills/tirith-migrate"

REFERENCES="schema validate verdicts terraform-plan other-providers variables install pipelines platform debug-ci"
EXAMPLE="examples/required-tags"
EXAMPLE_FILES="README.md policy.json should-fail.json should-pass.json"

# tirith-migrate, relative to its own pack root. One path per line so the list stays diffable.
MIGRATE_FILES="SKILL.md
reference/sentinel.md
reference/sentinel-corpus.md
examples/sentinel/README.md
examples/sentinel/restrict-instance-type/source.sentinel
examples/sentinel/restrict-instance-type/notes.md
examples/sentinel/restrict-instance-type/policy.json
examples/sentinel/restrict-instance-type/variables.json
examples/sentinel/restrict-instance-type/should-fail.json
examples/sentinel/restrict-instance-type/should-pass.json
examples/sentinel/mandatory-tags/source.sentinel
examples/sentinel/mandatory-tags/notes.md
examples/sentinel/mandatory-tags/policy.json
examples/sentinel/mandatory-tags/should-fail.json
examples/sentinel/mandatory-tags/should-pass.json
examples/sentinel/prevent-database-destroy/source.sentinel
examples/sentinel/prevent-database-destroy/notes.md
examples/sentinel/prevent-database-destroy/policy.json
examples/sentinel/prevent-database-destroy/should-fail.json
examples/sentinel/prevent-database-destroy/should-pass.json
examples/sentinel/prevent-database-destroy/should-fail-replacement.json
examples/sentinel/restrict-ssh-ingress/source.sentinel
examples/sentinel/restrict-ssh-ingress/notes.md
examples/sentinel/restrict-ssh-ingress/policy.json
examples/sentinel/restrict-ssh-ingress/should-fail.json
examples/sentinel/restrict-ssh-ingress/should-pass.json
examples/sentinel/restrict-ssh-ingress/diverges.json
examples/sentinel/require-private-registry-modules/source.sentinel
examples/sentinel/require-private-registry-modules/notes.md"

while [ $# -gt 0 ]; do
  case "$1" in
    --global) DEST="$HOME" ;;
    --cursor) CURSOR=1 ;;
    --ref)    REF="${2:?--ref needs a branch or tag}"; shift ;;
    -h|--help)
      sed -n '3,25p' "$0" 2>/dev/null | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) printf 'skill.sh: unknown option %s\n' "$1" >&2; exit 2 ;;
  esac
  shift
done

command -v curl >/dev/null 2>&1 || { echo "skill.sh: curl is required" >&2; exit 1; }

BASE="https://raw.githubusercontent.com/$REPO/$REF/$PACK"
TARGET="$DEST/$PACK"

# Download to a temporary directory first, then move into place. A half-written skill is
# worse than no skill: an agent will read whatever files exist and quietly work from a
# partial vocabulary.
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT INT TERM
mkdir -p "$TMP/reference" "$TMP/$EXAMPLE"

fetch() {
  curl -fsSL "$1" -o "$2" || { printf 'skill.sh: failed to download %s\n' "$1" >&2; exit 1; }
}

fetch "$BASE/SKILL.md" "$TMP/SKILL.md"
for f in $REFERENCES; do
  fetch "$BASE/reference/$f.md" "$TMP/reference/$f.md"
done
for f in $EXAMPLE_FILES; do
  fetch "$BASE/$EXAMPLE/$f" "$TMP/$EXAMPLE/$f"
done
MBASE="https://raw.githubusercontent.com/$REPO/$REF/$MIGRATE_PACK"
for f in $MIGRATE_FILES; do
  mkdir -p "$TMP/migrate/$(dirname "$f")"
  fetch "$MBASE/$f" "$TMP/migrate/$f"
done

mkdir -p "$TARGET/reference" "$TARGET/$EXAMPLE"
cp "$TMP/SKILL.md" "$TARGET/SKILL.md"
for f in $REFERENCES; do
  cp "$TMP/reference/$f.md" "$TARGET/reference/$f.md"
done
for f in $EXAMPLE_FILES; do
  cp "$TMP/$EXAMPLE/$f" "$TARGET/$EXAMPLE/$f"
done

MTARGET="$DEST/$MIGRATE_PACK"
for f in $MIGRATE_FILES; do
  mkdir -p "$MTARGET/$(dirname "$f")"
  cp "$TMP/migrate/$f" "$MTARGET/$f"
done

printf 'Installed the Tirith skill: %s\n' "$TARGET"
printf 'Installed the migration skill: %s\n' "$MTARGET"

if [ "$CURSOR" -eq 1 ]; then
  mkdir -p "$DEST/.cursor/rules"
  fetch "https://raw.githubusercontent.com/$REPO/$REF/.cursor/rules/tirith-policies.mdc" \
        "$TMP/tirith-policies.mdc"
  cp "$TMP/tirith-policies.mdc" "$DEST/.cursor/rules/tirith-policies.mdc"
  printf 'Installed the Cursor rule: %s\n' "$DEST/.cursor/rules/tirith-policies.mdc"
fi

printf 'Ask your agent to write a Tirith policy. It should name real condition types.\n'
