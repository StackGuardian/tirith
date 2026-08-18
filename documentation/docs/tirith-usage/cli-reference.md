---
id: cli-reference
title: CLI Reference
sidebar_label: CLI Reference
description: Every flag of the tirith command, what it prints, and how --json and --verbose change the output.
keywords:
  - tirith
  - cli
site_name: Tirith
slug: cli-reference/
---

The base `tirith` command evaluates a policy file against an input document, locally, on your own
machine. Nothing is sent anywhere and no account is needed.

```
tirith -policy-path policy.json -input-path plan.json
```

Run with no arguments, `tirith` prints its help text and exits `0`.

There is one subcommand, [`tirith platform check`](platform-check.md), which evaluates against the
policies a StackGuardian organization enforces instead of local files. It has its own flags and its own
page.

The flags below are this command's own. Beyond evaluating a single policy file they also cover using it
as a CI gate — a directory of policies, a masked input, and the verdict written out for a job to publish
— which has [its own page](evaluating-policy-files.md). Both surfaces write the same
[result document](output-contract.md).

## Flags

Note the spelling: the path and variable options take a **single dash** (`-policy-path`, not
`--policy-path`), while the output and behaviour switches take two.

| Flag | Argument | What it does |
|---|---|---|
| `-policy-path` | `PATH` | Path to the Tirith policy file. Required. |
| `-input-path` | `PATH` | Path to the document the policy is evaluated against. Required. |
| `-var-path` | `PATH` | Path to a JSON file of policy variables. Repeatable. |
| `-var` | `NAME=JSON` | One inline policy variable. Repeatable. |
| `--json` | | Print only the result document as JSON on stdout. |
| `--verbose` | | Show detailed (debug-level) logs from the run on stderr. |
| `--fail-on-error` | | Exit `3` when a policy fails, instead of `0`. Off by default. |
| `--version` | | Print the version and exit. |
| `-h`, `--help` | | Print the help text and exit. |

### `-policy-path`

The policy file to evaluate — a JSON document with `meta`, `evaluators` and an `eval_expression`.
See the [policy reference](../tirith-policies/tirith-policy-reference.md) for the schema, the
[evaluators reference](../tirith-reference/evaluators.md) for the available condition types, and the
[providers overview](../tirith-providers/overview.md) for what kinds of input each
`required_provider` reads.

If the flag is missing, `tirith` prints an error to stderr and exits `1`.

### `-input-path`

The document to evaluate: a terraform plan in JSON form (`terraform show -json tfplan`), a
Kubernetes manifest, an Infracost breakdown, or any JSON document — whatever the policy's provider
expects. Files ending in `.yaml` or `.yml` are parsed as YAML; a multi-document YAML file is read
as a list of documents. Everything else is parsed as JSON.

If the flag is missing, `tirith` prints an error to stderr and exits `1`.

### `-var-path` and `-var`

A policy can be parameterized with `{{ var.name }}` placeholders. These two flags supply the
values:

```
tirith -policy-path policy.json -input-path plan.json \
       -var-path common-vars.json -var 'max_cost=100'
```

- `-var-path` names a JSON file whose top-level keys are variable names. The flag may be repeated;
  files are merged in order, and a later file overrides an earlier one for the same key.
- `-var` supplies a single variable inline as `name=value`, where `value` is parsed as JSON — so
  `-var 'max_cost=100'` is a number, `-var 'region="eu-central-1"'` is a string, and
  `-var 'allowed=["a","b"]'` is a list. Inline variables are applied after all files, so they
  override them. A value that is not valid JSON is reported as an error and the variable is not
  set.

If the policy references a variable that none of these supplied, evaluation does not run at all:
the result carries only an `errors` entry (`Variables not found: ...`), and with
`--fail-on-error` the exit code is `1` — the tool could not evaluate, which is different from a
policy failing.

### `--json`

Prints the result document, and nothing else, to stdout — all logging is disabled, so the output
can be piped straight into `jq` or another program:

```
tirith -policy-path policy.json -input-path plan.json --json | jq .final_result
```

The document has this shape:

```json
{
   "meta": { "version": "v1", "required_provider": "stackguardian/json" },
   "final_result": true,
   "evaluators": [
      {
         "id": "check1",
         "passed": true,
         "result": [ { "passed": true, "message": "1 is equal to 1", "meta": null } ],
         "description": null
      }
   ],
   "errors": [],
   "eval_expression": "check1"
}
```

`final_result` is tri-state: `true` when every check that ran passed, `false` when a check ran and
failed, and `null` when every check was skipped (see
[error tolerance](../tirith-policies/tirith-policy-error-tolerance.md)) — the policy then evaluated
nothing. Each evaluator's `passed` is tri-state in the same way. If evaluation throws an
unexpected error under `--json`, the command prints an empty `{}` and exits `1`.

The exit code does not change under `--json`; combine it with `--fail-on-error` to gate on the
verdict while still capturing the document.

### `--verbose`

Without it, the run prints the pretty-printed per-check results on stdout and only messages at
INFO level and above on stderr, formatted as `[LEVEL] message`. With `--verbose`, stderr carries
debug-level logs in a long format that includes the timestamp, process id and source location —
useful when a policy is not matching what you expect and you want to see each evaluator being
processed.

`--verbose` has no effect together with `--json`, which disables logging entirely.

### `--fail-on-error`

By default the command exits `0` whenever it completed the evaluation, whether the policy passed
or failed — the verdict is in the output. `--fail-on-error` turns the exit code into a gate: `3`
when a policy failed, `1` when nothing could be evaluated, `0` only when every check that ran
passed. This is the flag that makes the command usable as a CI gate; the full contract is on the
[exit codes](exit-codes.md) page.

### `--version`

Prints the version number (for example `1.2.0`) and exits `0`.

## Output streams

- **stdout** carries the result: the pretty-printed report by default, or the JSON document under
  `--json`.
- **stderr** carries logs and error messages.

This split is deliberate so that redirecting stdout captures only the verdict.
