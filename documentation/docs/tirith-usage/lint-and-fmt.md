---
id: lint-and-fmt
title: Lint and format
sidebar_label: Lint and format
description: tirith lint checks policy files for mistakes that would gate nothing or fail as a false violation. tirith fmt rewrites them into one canonical layout. Neither needs a plan document.
keywords:
  - tirith
  - lint
  - fmt
  - format
  - pre-commit
site_name: Tirith
slug: lint-and-fmt/
---

Two commands that read policy files and nothing else. Neither needs a plan document, an account,
or a network call, which is what lets them run in a pre-commit hook and in a slim CI image without
the optional `tui` extra.

```bash
tirith lint .tirith/policies    # is the policy well formed?
tirith fmt .tirith/policies     # rewrite it into the canonical layout
```

:::note Not in 1.2.0
Both commands are on `main` and will arrive in the next release. To use them today, install from
the branch rather than the `1.2.0` tag:

```bash
pip install "git+https://github.com/StackGuardian/tirith.git@main"
```
:::

## `tirith lint`

Lint checks the **shape**, not the meaning. It runs the same validator the
[interactive interface](interactive-interface.md) runs on every keystroke, so the two never
disagree, and it catches the class of mistake that otherwise reaches CI looking like a real
infrastructure violation:

- a condition `type` that does not exist, against the closed list of
  [thirteen conditions](../tirith-reference/evaluators.md)
- a `provider_args` key that belongs to a different provider than the one in
  `meta.required_provider`
- an evaluator that `eval_expression` never names, so it is computed and then discarded
- `error_tolerance` placed on the evaluator instead of inside `condition`, where it is silently
  ignored and the check still fails

What lint cannot tell you is whether a well-formed policy matches anything. Only evaluating it
against a document that *should* fail answers that:

```bash
tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error
```

### Usage

```
tirith lint [PATH ...] [--json] [--strict] [--quiet]
```

| Flag | What it does |
|---|---|
| `--json` | Print the report as a JSON document instead of text |
| `--strict` | Treat warnings as errors when deciding the exit code |
| `--quiet` | Print findings only, with no summary line and no skipped files |

Findings are printed one per line, in a form an editor or a log scraper can parse:

```
.tirith/policies/s3.json:evaluators[0].condition: error: unknown condition type 'EqualTo'
.tirith/policies/s3.json:eval_expression: warning: evaluator 'bucket_acl' is never referenced
2 policies, 1 errors, 1 warnings
```

`--json` returns the same report structured, so an editor integration or another program does not
have to parse the text:

```json
{
  "files": [
    {
      "path": ".tirith/policies/s3.json",
      "findings": [
        {"severity": "error", "where": "evaluators[0].condition", "message": "unknown condition type 'EqualTo'"}
      ]
    }
  ],
  "skipped": [],
  "missing": [],
  "summary": {"policies": 2, "errors": 1, "warnings": 1, "ignored": 0},
  "exit_status": 3
}
```

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Every policy is clean |
| `3` | A policy has an error-level finding, or a warning under `--strict` |
| `1` | A path does not exist, or nothing was found to lint |

`3` rather than `1` for a bad policy is deliberate, and matches the rest of Tirith: the linter
saying no about a policy is a verdict, not a tool failure. See [exit codes](exit-codes.md).

## `tirith fmt`

Format rewrites a policy into one canonical layout, so that two people writing the same policy
produce the same bytes and a diff shows a change of meaning rather than a change of key order.

It reorders keys and normalises whitespace. It never changes a value, adds a key, or reorders a
list, and the result parses back to a document equal to the one it read.

### Usage

```
tirith fmt [PATH ...] [--check] [--diff]
```

| Flag | What it does |
|---|---|
| `--check` | Do not write. Exit `3` if any file would change |
| `--diff` | Print a unified diff of what would change. Implies `--check` |

With no flags it rewrites the files in place and prints the path of each one it changed.

### The layout

Whitespace is exactly `json.dumps(indent=2, ensure_ascii=False)` plus one trailing newline, which
means a policy written by any tool using the Python standard library is already canonical without
knowing `fmt` exists. Non-ASCII characters stay as written rather than being escaped.

Keys are ordered:

| Object | Order |
|---|---|
| top level | `$schema`, `meta`, `evaluators`, `eval_expression` |
| `meta` | `version`, `required_provider`, `id`, `name`, `description`, `severity`, `enforcement`, `tags`, `remediation` |
| each evaluator | `id`, `description`, `provider_args`, `condition` |
| `provider_args` | `operation_type` first, then the provider's own keys in their original order |
| `condition` | `type`, `value`, `error_tolerance` |

A key the document has that is not in these lists keeps its original relative order after the
listed ones, so an unrecognised key is preserved rather than dropped or sorted somewhere
surprising.

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Nothing to change, or the changes were written |
| `3` | `--check` found files that would change |
| `1` | A path is missing, a file is not valid JSON, or nothing was found |

## Which files they read

Both commands take any number of paths, and both default to the same place when given none:
`.tirith/policies` if that directory exists, otherwise the current directory.

A directory is searched recursively for `*.json`. A **policy** is a JSON object with at least one
of the three top-level keys the engine reads, `meta`, `evaluators` or `eval_expression`; anything
else that parses as JSON is left alone. That is what lets you point either command at a directory
that also holds a `package.json` or a plan document without producing findings about files that
were never policies.

- A JSON file named **explicitly on the command line** that is not a policy is reported as skipped
  by name, so a typo'd path to a plan document does not read as a clean run.
- A JSON file met **while walking a directory** that is not a policy is counted rather than
  listed. Input documents living beside their policies are expected there.
- A `.json` file inside a policy directory that does not parse at all is reported as an error, not
  ignored. An unparseable policy is a defect.

These directories are never descended into: `.git`, `.terraform`, `node_modules`, `__pycache__`,
`.venv`, `venv`. Note that `.tirith` is deliberately not among them, since that is where policies
conventionally live and skipping dot-directories wholesale would skip the one that matters.

## In a pre-commit hook

This repository publishes both commands as hooks, so a commit that touches one policy lints and
formats that one policy:

```yaml title=".pre-commit-config.yaml"
repos:
  - repo: https://github.com/StackGuardian/tirith
    rev: main
    hooks:
      - id: tirith-lint
      - id: tirith-fmt
```

```bash
pre-commit install
pre-commit run --all-files
```

Both hooks match `.tirith/*.json` and `*.tirith.json` by default. Override `files` if your
policies live somewhere else.

Linting at commit time rather than evaluating is a deliberate choice. Evaluating needs a plan
document, and producing one means running `terraform plan`, which is too slow for a commit hook
and needs cloud credentials a hook has no business holding. See
[CI integration](ci-integration.md) for the full argument, and for where evaluation belongs.

## In CI

`fmt --check` is the CI shape, next to whatever else already checks formatting:

```bash
tirith fmt --check .tirith/policies
tirith lint .tirith/policies
```

Both exit `3` on a finding, so a pipeline that already distinguishes `3` from `1` treats a badly
formatted or invalid policy exactly as it treats a policy violation, and a missing path as the
tooling problem it is.
