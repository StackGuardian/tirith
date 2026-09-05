---
id: agent-skills
title: Agent Skills
sidebar_label: Agent Skills
description: Install the Tirith skill pack so a coding agent writes policies from the real vocabulary instead of inventing condition types that look plausible.
keywords:
  - tirith
  - agent
  - skill
  - claude
  - cursor
  - agents.md
  - copilot
site_name: Tirith
slug: agent-skills/
---

An agent asked for a Tirith policy will produce one. The JSON will be well formed, the keys will
look right, and it will very often be wrong in a way that reads as correct: a condition type named
`Matches` or `Exists`, neither of which exists, or the argument key from a different provider.

That failure is quiet. The policy parses, the evaluator does not match, and the check reports a
pass. **A rule that gates nothing looks exactly like a rule that found nothing wrong.**

The skill pack fixes the cause: it gives the agent the closed vocabulary instead of leaving it to
guess from a plausible-looking shape.

## Install it

```bash
curl -fsSL https://stackguardian.github.io/tirith/skill.sh | sh
```

Two skills under `.claude/skills/`: `tirith-policies`, for writing policies, and `tirith-migrate`,
for translating existing Sentinel policies. No config file, and they are picked up in any
repository you copy them into. A session that is already running may not see a newly installed
skill until it is restarted; a new session sees it immediately.

| Flag | |
|---|---|
| `--cursor` | Also install `.cursor/rules/tirith-policies.mdc`, scoped with globs |
| `--global` | Install into `~/.claude/skills/` instead of this repository |
| `--ref REF` | Install from a branch or tag instead of `main` |
| `--help` | The same summary, from the script itself |

The script downloads those files and does nothing else: no package is installed, no
`PATH` is changed, nothing is executed after the download, and it never touches a file it did not
create. It downloads to a temporary directory and moves the files into place only once all of them
have arrived, because a half-written skill is worse than none: an agent reads whatever files exist
and works from a partial vocabulary without saying so.

It is [a committed file in this repository](https://github.com/StackGuardian/tirith/blob/main/documentation/static/skill.sh)
served from the same origin as this page, so the thing you pipe into a shell is the thing you can
read first.

### Cursor

```bash
curl -fsSL https://stackguardian.github.io/tirith/skill.sh | sh -s -- --cursor
```

Cursor reads a single rule file scoped with globs, so it attaches by itself the moment a policy
file is open and stays out of the way otherwise.

### Codex, Zed, and anything reading `AGENTS.md`

```bash
curl -fsSL https://stackguardian.github.io/tirith/skill.sh | sh
printf '\n## Tirith policies\nSee .claude/skills/tirith-policies/SKILL.md\n' >> AGENTS.md
```

One file at the repository root is read by a growing number of clients, and the pack beside it
keeps the references resolvable.

## Check it worked

Ask for a policy in plain words: *every bucket needs an Owner tag*. With the pack loaded your agent
names a real condition type and the argument key that provider actually takes. Without it, it
invents one that reads perfectly and gates nothing.

## What is in the pack

`SKILL.md` is the entry point and is loaded first; the references are read on demand, so a client
with a small context window pays for only what the task needs.

| File | |
|---|---|
| `SKILL.md` | Turning an intent into valid policy JSON: provider, operation, condition, expression |
| `reference/schema.md` | The closed vocabulary. Thirteen condition types, each provider's operations, and the argument key that differs per provider |
| `reference/validate.md` | The mistakes that produce a policy which looks right and gates nothing |
| `reference/verdicts.md` | Reading a result document and an exit code |
| `reference/terraform-plan.md` | The Terraform and OpenTofu plan provider |
| `reference/other-providers.md` | Kubernetes, Infracost, JSON and StackGuardian Workflow |
| `reference/variables.md` | One policy across environments |
| `reference/install.md` | Installing Tirith, and why the install is a git URL |
| `reference/pipelines.md` | Adding the gate to six CI platforms |
| `reference/platform.md` | Evaluating an organization's policies |
| `reference/debug-ci.md` | Diagnosing a red check |
| `examples/required-tags/` | A policy, a plan that fails it and a plan that passes it, so the agent can prove its own work before it hands it back |

## Migrating from Sentinel

The second skill, `tirith-migrate`, is for teams with existing HashiCorp Sentinel policies. It is a
projection from a larger language onto a smaller one, and the skill's job is to say what survives.
Measured against the 110 policies in HashiCorp's public libraries, 41 translate exactly, 40
approximately, and 29 not at all. Each translation is tagged with that fidelity, every approximate
one ships a plan on which Sentinel and Tirith disagree, and every impossible one is refused in
words with the Tirith issue that would change it. Checkov and OPA/Rego are planned next.

## Two things decide whether the policy actually works

The pack teaches vocabulary. It does not run anything, and it is not a substitute for evaluating
the policy:

1. **Give the agent `tirith` on `PATH`.** It is an ordinary command, so an agent with a shell can
   evaluate its own work without a protocol server or a plugin. See
   [Quick Installation](../tirith-installation/quick-intallation.md).
2. **Give it a document that should fail.** Ask for the policy *and* a plan that violates it, then
   check the exit code is `3`. If it is `0`, the policy matched nothing, which is the failure this
   whole page exists to prevent. The pack ships a starting pair in `examples/required-tags/`.
   See [Exit codes](exit-codes.md).

## Keeping it current

The pack is a copy, so it does not update itself. Re-run the installer to take the current
version:

```bash
curl -fsSL https://stackguardian.github.io/tirith/skill.sh | sh
```

Re-running is safe: it overwrites the files it owns, in both skills, and leaves everything else alone.

`--ref` takes a branch or a commit, which is worth knowing for a fork or a pull request. It cannot
yet take a release tag: the pack was added after `1.2.0`, so `main` is the only ref that has it,
and asking for a tag that predates it fails with exit `1` rather than installing something
incomplete.
