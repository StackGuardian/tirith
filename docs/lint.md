# `tirith lint` and `tirith fmt`

Check policy files for the mistakes that otherwise reach CI looking like real infrastructure
violations, and keep them in one layout. Neither needs a plan document, the platform, or the
`tui` extra, so both fit in a pre-commit hook and a slim CI image.

## What lint checks

The same validator the interactive interface runs on every keystroke, reading the engine's own
registries rather than a copy of them:

| Finding | Severity | Why it matters |
| --- | --- | --- |
| `condition.type` is not one of the thirteen evaluators | error | The engine fails the check with a message, exit 3, and `errors` stays empty; a job sees a violation |
| `meta.required_provider` missing or unknown | error | The engine looks for a provider named `core`, which does not exist |
| `provider_args.operation_type` missing or not one the provider has | error | |
| A required argument of the operation missing | error | |
| A `provider_args` key the operation does not read | warning | Ignored rather than rejected, so the check reads nothing and passes |
| `error_tolerance` on the evaluator instead of inside `condition` | error | Ignored silently; the check fails as if no tolerance were set |
| An evaluator id the expression never names | warning | It runs but cannot affect the verdict |
| A name in the expression that is not an evaluator id | error | Dropped from the expression, or a hard failure if it contains a hyphen |
| A single `&` or `\|` in the expression | error | Only `&&` and `\|\|` are operators |
| `condition.value` missing for a type that needs one, or an invalid regex | error | |
| A key the engine does not read, at any level | warning | Usually a typo |

What it cannot check: whether the policy matches anything. A policy whose `terraform_resource_type`
names a type the plan never contains is well-formed and gates nothing. Evaluate it against a document
that should fail and check for exit `3`.

## Exit codes

| Code | `lint` | `fmt` |
| --- | --- | --- |
| 0 | Every policy is clean (warnings allowed unless `--strict`) | Nothing to change, or files were written |
| 3 | A policy has errors | `--check`: a file would change |
| 1 | A path does not exist, or no policies were found | A path does not exist, a file is not valid JSON, or no policies were found |

`3` rather than `1` for a bad policy is deliberate and matches evaluation: the linter saying no
about a policy is a verdict. `1` is reserved for the tool being unable to do its job.

## Which files

A path may be a file or a directory. Directories are walked for `*.json`; a JSON document is a
policy when it has any of `meta`, `evaluators` or `eval_expression` at the top level, so the plan
documents that sit beside policies in an examples directory are ignored and counted, not
reported. A file named explicitly that turns out not to be a policy is reported as skipped. With
no path, both commands use `.tirith/policies` if it exists, otherwise the current directory.

## The canonical layout

`fmt` orders keys and normalises whitespace. It never changes a value, adds or removes a key, or
reorders a list, and the output parses back to an equal document.

- Top level: `meta`, `evaluators`, `eval_expression`. A `$schema` key comes first if present.
- `meta`: `version`, `required_provider`, `id`, `name`, `description`, `severity`, `enforcement`, `tags`, `remediation`.
- Each evaluator: `id`, `description`, `provider_args`, `condition`. `operation_type` leads `provider_args`; `type`, `value`, `error_tolerance` is the order inside `condition`.
- Keys not in these lists keep their relative order after the listed ones.
- Whitespace is exactly Python's `json.dumps(indent=2, ensure_ascii=False)` plus one trailing newline, so a policy written by any tool that uses the standard library is already canonical. Non-ASCII stays as written.

## Pre-commit

```yaml
repos:
  - repo: https://github.com/StackGuardian/tirith
    rev: main          # or a tag that includes lint
    hooks:
      - id: tirith-lint
      - id: tirith-fmt
```

The hooks run on files under `.tirith/` and on `*.tirith.json`. Override `files:` if your policies
live elsewhere.

## `tirith lint --help`

```
usage: tirith lint [-h] [--json] [--strict] [--quiet] [PATH ...]

Check Tirith policy files for mistakes that would otherwise gate nothing or fail as a false violation.

positional arguments:
  PATH        Policy files or directories.

options:
  -h, --help  show this help message and exit
  --json      Print findings as a JSON document instead of text.
  --strict    Treat warnings as errors for the exit code.
  --quiet     Print findings only, no summary and no skipped files.

With no path, lints .tirith/policies if it exists, otherwise the current directory.
Directories are searched for *.json files; JSON that is not a policy is skipped.

Exit codes:  0 every policy is clean   3 a policy has errors   1 a path is missing or nothing was found

Lint checks the shape. Only evaluating against a document that should fail checks the meaning:
    tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error
```

## `tirith fmt --help`

```
usage: tirith fmt [-h] [--check] [--diff] [PATH ...]

Rewrite Tirith policy files into the canonical layout.

positional arguments:
  PATH        Policy files or directories.

options:
  -h, --help  show this help message and exit
  --check     Do not write. Exit 3 if any file would change.
  --diff      Print a unified diff of the changes. Implies --check.

With no path, formats .tirith/policies if it exists, otherwise the current directory.
Keys are ordered meta, evaluators, eval_expression; inside a check id, description,
provider_args, condition. Values and list order are never changed.

Exit codes:  0 nothing to change (or written)   3 --check found files that would change
             1 a path is missing, a file is not valid JSON, or nothing was found
```
