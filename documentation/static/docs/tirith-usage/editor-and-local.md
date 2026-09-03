# In your editor

Source: https://stackguardian.github.io/tirith/docs/tirith-usage/editor-and-local/
Summary: In development — VS Code tasks, a pre-commit hook, and the local loop to use when an AI agent is drafting the policy. The lint half is not in the released package yet.

[WARNING] In development — the lint half has not shipped

`tirith lint`, the pre-commit hook and the VS Code tasks below are **in development**. They are
not in the released package: `pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"`
gives you `tirith`, `tirith ui` and `tirith platform check`, and no `lint` subcommand. The
`tirith-lint` hook id and the task file are not in the repository yet either.

**What works today** is the second half of the loop — evaluating a policy against a document with
`tirith -policy-path … -input-path … --fail-on-error`. That runs locally, offline, on any
installed version.

This page is published now so the shape is reviewable. Follow
[the repository](https://github.com/StackGuardian/tirith) for the release, or
[tell us what the loop is missing](https://github.com/StackGuardian/tirith/issues/new/choose).

CI is the last place a policy should fail. This page is about the loop before that — running
Tirith on your own machine, while the code is still being written.

It matters most when an agent is drafting the policy for you. Generated policy JSON is plausible
by construction: it parses, it looks right, and a policy that matches nothing is indistinguishable
from one that works until you evaluate it.

## The loop

```bash
tirith lint .tirith/policies                                                  # shape — in dev
tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error    # meaning — ships
```

Linting checks the **shape** — that every condition type exists, that no `provider_args` key
belongs to a different provider, that `eval_expression` names every evaluator. Only evaluation
checks the **meaning**.

Run both against a document that *should* fail. A guardrail only ever seen passing is a guardrail
nobody has tested.

## VS Code tasks

**In development.** The lint task below calls a subcommand the released package does not have; the
evaluate task works today.

Drop this in `.vscode/tasks.json` and the loop becomes one keystroke:

```json
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

**In development.** The `tirith-lint` hook id is not published yet, so this configuration will not
resolve — `pre-commit` fails with an unknown hook rather than installing anything.

```yaml
repos:
  - repo: https://github.com/StackGuardian/tirith
    rev: 1.2.0
    hooks:
      - id: tirith-lint
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
curl -fsSL https://stackguardian.github.io/tirith/skill.sh | sh
```

Add `--cursor` for the Cursor rule. [Agent Skills](agent-skills.md) covers what is in the pack,
the other clients, and how to tell whether it took effect.

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
