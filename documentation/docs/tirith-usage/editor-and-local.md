---
id: editor-and-local
title: In your editor
sidebar_label: In your editor
description: VS Code tasks, a pre-commit hook, and the local loop to use when an AI agent is drafting the policy.
keywords:
  - tirith
  - vscode
  - pre-commit
  - local
  - agent
site_name: Tirith
slug: editor-and-local/
---

:::note Not in 1.2.0

`tirith lint`, `tirith fmt` and the pre-commit hooks are on `main` and will be in the next
release. `pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"` does not have them;
install from `main` until then.

:::

CI is the last place a policy should fail. This page is about the loop before that — running
Tirith on your own machine, while the code is still being written.

It matters most when an agent is drafting the policy for you. Generated policy JSON is plausible
by construction: it parses, it looks right, and a policy that matches nothing is indistinguishable
from one that works until you evaluate it.

## The loop

```bash
tirith lint .tirith/policies                                                  # shape
tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error    # meaning
```

Linting checks the **shape** — that every condition type exists, that no `provider_args` key
belongs to a different provider, that `eval_expression` names every evaluator. Only evaluation
checks the **meaning**.

Run both against a document that *should* fail. A guardrail only ever seen passing is a guardrail
nobody has tested.

## VS Code tasks

Drop this in `.vscode/tasks.json` and the loop becomes one keystroke:

```json title=".vscode/tasks.json"
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Tirith: lint policies",
      "type": "shell",
      "command": "tirith lint .tirith/policies",
      "problemMatcher": [],
      "group": "test"
    },
    {
      "label": "Tirith: check the plan",
      "type": "shell",
      "command": "tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error",
      "problemMatcher": [],
      "group": {"kind": "test", "isDefault": true},
      "dependsOn": ["Tirith: lint policies"]
    }
  ]
}
```

`Tirith: check the plan` is the default test task, so **⇧⌘B** / **Ctrl+Shift+B** runs the whole
loop. The complete file — including a task to refresh `plan.json` and one to open the result in
the interactive explorer — is
[`.vscode/tasks.json`](https://github.com/StackGuardian/tirith/blob/main/.vscode/tasks.json).

## Catch it at commit time

```yaml title=".pre-commit-config.yaml"
repos:
  - repo: https://github.com/StackGuardian/tirith
    rev: main          # 1.2.0 predates the hooks; pin the first tag that includes them
    hooks:
      - id: tirith-lint
      - id: tirith-fmt
```

```bash
pre-commit install
```

The hook runs only when a policy file changes, needs no network, and exits `3` when a policy has
an error. See [CI integration](ci-integration.md) for why it lints rather than evaluates.

## When an agent is writing the policy

Install the Tirith skill and your agent gets the closed condition list, the argument key each
provider reads, and the instruction to run a policy before claiming it works:

```bash
mkdir -p .claude/skills/tirith-policies/reference
BASE=https://raw.githubusercontent.com/StackGuardian/tirith/main/.claude/skills/tirith-policies
curl -sL $BASE/SKILL.md -o .claude/skills/tirith-policies/SKILL.md
```

Cursor reads `.cursor/rules/tirith-policies.mdc` instead, scoped with globs so it attaches by
itself when a policy file is open.

Two things make the difference between a drafted policy and a working one:

1. **The agent has `tirith` on PATH.** It is an ordinary command, so an agent with a shell can
   lint and evaluate its own work without any protocol server or plugin.
2. **You give it a document that should fail.** Ask for the policy *and* a plan that violates it,
   then check that the exit code is `3`. If it is `0`, the policy matched nothing.

## Reading a failure without leaving the terminal

```bash
tirith --json -policy-path .tirith/policies -input-path plan.json > result.json
tirith ui --result result.json      # needs the optional [tui] extra
```

The explorer names the resource behind each finding — its address, the planned action, and the
attributes that changed — which the pretty printer does not show. See
[the interactive interface](interactive-interface.md).
