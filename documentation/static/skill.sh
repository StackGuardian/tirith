#!/usr/bin/env sh
#
# Install the Tirith skills for a coding agent.
#
#   curl -fsSL https://stackguardian.github.io/tirith/skill.sh | sh
#
# Read this file before you run it. It is served over HTTPS from the documentation site and
# its source is documentation/static/skill.sh in StackGuardian/tirith, so the version you
# are about to pipe into a shell is the version you can read in the repository.
#
# What it does: downloads one archive of the repository at REF, copies every skill under
# .claude/skills/ out of it into ./.claude/skills/ (tirith-policies, tirith-standards,
# tirith-migrate today) and, with --cursor, one rule file into .cursor/rules/. It creates
# directories, writes those files, and nothing else. No package is installed, no PATH is
# changed, nothing is executed after the download, and it never touches a file it did not
# create. One request rather than one per file: the first version fetched each file from
# raw.githubusercontent.com and took ten minutes on a slow link.
#
# Flags:
#   --global   install into ~/.claude/skills/ instead of ./.claude/skills/
#   --cursor   also install the Cursor rule into .cursor/rules/
#   --ref REF  install from a branch or tag instead of main
#
# POSIX sh on purpose: it runs under dash, ash and busybox, which is what a slim CI image
# gives you. Needs curl and tar.

set -eu

REPO="StackGuardian/tirith"
REF="main"
DEST="."
CURSOR=0

while [ $# -gt 0 ]; do
  case "$1" in
    --global) DEST="$HOME" ;;
    --cursor) CURSOR=1 ;;
    --ref)    REF="${2:?--ref needs a branch or tag}"; shift ;;
    -h|--help)
      sed -n '3,26p' "$0" 2>/dev/null | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) printf 'skill.sh: unknown option %s\n' "$1" >&2; exit 2 ;;
  esac
  shift
done

command -v curl >/dev/null 2>&1 || { echo "skill.sh: curl is required" >&2; exit 1; }
command -v tar  >/dev/null 2>&1 || { echo "skill.sh: tar is required" >&2; exit 1; }

# The archive URL can be overridden for testing against a local `git archive` tarball.
ARCHIVE="${TIRITH_SKILL_ARCHIVE:-https://codeload.github.com/$REPO/tar.gz/refs/heads/$REF}"

# Everything lands in a temporary directory first and is copied into place only once the
# archive has been read in full. A half-written skill is worse than no skill: an agent will
# read whatever files exist and quietly work from a partial vocabulary.
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT INT TERM

if ! curl -fsSL "$ARCHIVE" -o "$TMP/repo.tar.gz"; then
  # A tag lives under refs/tags, a branch under refs/heads; try the other before giving up.
  ALT="https://codeload.github.com/$REPO/tar.gz/refs/tags/$REF"
  [ -n "${TIRITH_SKILL_ARCHIVE:-}" ] || curl -fsSL "$ALT" -o "$TMP/repo.tar.gz" || {
    printf 'skill.sh: could not download %s (ref %s)\n' "$REPO" "$REF" >&2; exit 1; }
fi

mkdir -p "$TMP/x"
tar -xzf "$TMP/repo.tar.gz" -C "$TMP/x"
# GitHub archives have one top-level directory named after the ref; a `git archive` tarball
# has none. Find the skills directory wherever it landed, at most one level down.
SRC=""
for candidate in "$TMP/x/.claude/skills" "$TMP"/x/*/.claude/skills; do
  [ -d "$candidate" ] && { SRC="$candidate"; break; }
done
[ -n "$SRC" ] || { printf 'skill.sh: the archive for ref %s has no .claude/skills directory\n' "$REF" >&2; exit 1; }
ROOT="$(dirname "$(dirname "$SRC")")"

TARGET="$DEST/.claude/skills"
mkdir -p "$TARGET"
installed=0
for pack in "$SRC"/*/; do
  name="$(basename "$pack")"
  [ -f "$pack/SKILL.md" ] || continue
  # Replace the pack wholesale so a file dropped upstream does not linger here.
  rm -rf "$TARGET/$name"
  cp -R "$pack" "$TARGET/$name"
  printf 'Installed %s: %s\n' "$name" "$TARGET/$name"
  installed=$((installed + 1))
done
[ "$installed" -gt 0 ] || { echo "skill.sh: no skills found in the archive" >&2; exit 1; }

if [ "$CURSOR" -eq 1 ]; then
  RULE="$ROOT/.cursor/rules/tirith-policies.mdc"
  [ -f "$RULE" ] || { echo "skill.sh: the archive has no .cursor/rules/tirith-policies.mdc" >&2; exit 1; }
  mkdir -p "$DEST/.cursor/rules"
  cp "$RULE" "$DEST/.cursor/rules/tirith-policies.mdc"
  printf 'Installed the Cursor rule: %s\n' "$DEST/.cursor/rules/tirith-policies.mdc"
fi

printf 'Ask your agent to write a Tirith policy. It should name real condition types.\n'
