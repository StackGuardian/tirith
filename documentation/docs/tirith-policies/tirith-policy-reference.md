---
id: tirith-policy-reference
title: Policy Reference
sidebar_label: Policy Reference
description: Field-by-field reference for the Tirith policy file format, including every key, its type, its default, and its failure behavior.
keywords:
  - tirith
site_name: Tirith
slug: tirith-policy-reference/
---

A Tirith policy is a single JSON document with exactly three top-level keys. It is evaluated against an input document passed to the CLI with `-input-path` (see the [CLI reference](../tirith-usage/cli-reference.md)). The policy file itself is always JSON; the input file is parsed as JSON unless its name ends in `.yaml` or `.yml`, in which case it is parsed as YAML (a multi-document YAML file becomes a list of documents).

```json title="policy.json"
{
  "meta": {
    "version": "v1",
    "required_provider": "stackguardian/json"
  },
  "evaluators": [
    {
      "id": "can_post",
      "provider_args": {
        "operation_type": "get_value",
        "key_path": "verb"
      },
      "condition": {
        "type": "Equals",
        "value": "POST"
      }
    }
  ],
  "eval_expression": "can_post"
}
```

Unknown keys, at any level, are ignored.

## Top-level keys

| Key | Required | Type | Description |
|---|---|---|---|
| `meta` | yes | object | Policy metadata. Selects the provider; everything else is informational. |
| `evaluators` | yes | array of objects | The checks. Each one extracts values from the input and compares them against a condition. |
| `eval_expression` | yes | string | Boolean expression over evaluator `id`s that produces the final verdict. |

If `meta`, `evaluators`, or `eval_expression` is missing, the run aborts before producing a verdict: the CLI prints `ERROR` and exits with code `1` (with or without `--fail-on-error`).

## `meta`

| Key | Required | Type | Default | Behavior |
|---|---|---|---|---|
| `required_provider` | effectively yes | string | `"core"` | Selects the provider used by every evaluator in the policy. See [below](#metarequired_provider). |
| `version` | no | string | none | Not interpreted. Always echoed into the result `meta` (as `null` when absent). |
| `id` | no | any (conventionally string) | none | Not interpreted. Echoed verbatim into the result `meta` only when present. |
| `name` | no | any (conventionally string) | none | Same as `id`. |
| `description` | no | any (conventionally string) | none | Same as `id`. |
| `severity` | no | any (conventionally string) | none | Same as `id`. |
| `enforcement` | no | any (conventionally string) | none | Same as `id`. See [below](#metaenforcement). |
| `tags` | no | any (conventionally array of strings) | none | Same as `id`. |
| `remediation` | no | any (conventionally string) | none | Same as `id`. |

An empty `meta` object (`"meta": {}`) is accepted; the policy then falls back to the default provider, which fails every check (see next section).

### `meta.required_provider`

The registered providers are:

- `stackguardian/terraform_plan`
- `stackguardian/infracost`
- `stackguardian/sg_workflow`
- `stackguardian/json`
- `stackguardian/kubernetes`

Each provider defines its own `provider_args`; see the [provider documentation](../tirith-providers/overview.md).

When `required_provider` is absent it defaults to `"core"`, and no provider named `core` is registered. An unregistered provider name — the default included — is **not** a hard error: every evaluator in the policy simply receives no values and fails with the message `Could not find input value`. The final verdict is a failure (exit code `3` under `--fail-on-error`), which can be mistaken for a genuine policy violation. Always set `required_provider` explicitly.

### `meta.enforcement`

The open-source engine does **not** interpret this field. There is no list of accepted values, no validation, and no warning: any value — `hard_mandatory`, `soft_mandatory`, or any other string — is copied verbatim into the result `meta` and changes nothing about how the policy is evaluated. An unrecognised value has exactly the same effect as a recognised-looking one: none.

In particular, `enforcement` never affects the exit code of the `tirith` command. The exit code is determined solely by `final_result` and the `--fail-on-error` flag (see [Outcomes and exit codes](#outcomes-and-exit-codes)). If you need a policy to block a pipeline *when invoking the CLI directly*, gate on the exit code with `--fail-on-error`, not on this field. The same applies to `severity`, `tags`, and `remediation`: they exist so that tools consuming Tirith's JSON output can act on them, and the engine passes them through untouched.

:::note Consumers do interpret it

The field is not decorative — it is read by the layer above the engine. The
[GitHub Action](../tirith-usage/ci-integration.md) downgrades a failing policy to a warning when
`meta.enforcement` is one of `soft_mandatory`, `advisory`, `warn`, `warning`, `low` or
`approval_required`, and blocks on `hard_mandatory`, `mandatory`, `fail`, `error`, `high`,
`critical` or `blocking`. Matching is case-insensitive and ignores surrounding whitespace.

An **unrecognised** value blocks, and logs a warning that it did so. That is deliberate: a policy
that is mislabelled or carries a typo must gate rather than slip through silently.

So `enforcement` is meaningful when a consumer acts on it, and inert when you run `tirith` yourself.
:::

## `evaluators[]`

Each entry in the `evaluators` array is an object with these keys:

| Key | Required | Type | Default | Behavior |
|---|---|---|---|---|
| `id` | yes | string | — | The name this check is referenced by in `eval_expression`. Missing `id` aborts the run (`ERROR`, exit `1`). |
| `provider_args` | yes | object | — | Arguments for the provider selected by `meta.required_provider`. Missing `provider_args` aborts the run (`ERROR`, exit `1`). |
| `condition` | yes | object | — | The comparison applied to every value the provider extracts. Missing `condition` aborts the run (`ERROR`, exit `1`). |
| `description` | no | string | none | Informational. Echoed into the result for this check (as `null` when absent). |

`id` is substituted into `eval_expression` as a bare word, so it must look like an identifier: letters, digits, and underscores. Ids should be unique within a policy; if two evaluators share an id, both appear in the output but only the **last** one's outcome is substituted into `eval_expression`.

### `evaluators[].provider_args`

The contents are provider-specific; the one key every provider expects is `operation_type`, which selects the operation (for example `get_value` for `stackguardian/json`, or `attribute` for `stackguardian/terraform_plan`). See [providers](../tirith-providers/overview.md) for each provider's operations and arguments.

A malformed `provider_args` — an unsupported `operation_type`, or a missing required argument — does not abort the run. The provider reports the mistake as an error on that check, the check fails regardless of `error_tolerance`, and the message tells you what was wrong (for example `operation_type: 'attrbute' is not supported (severity_value: 99)`).

### `evaluators[].condition`

| Key | Required | Type | Default | Behavior |
|---|---|---|---|---|
| `type` | yes | string | — | The condition (evaluator) name. An unknown or missing `type` does not abort the run: that check fails with `` `X` is not a supported evaluator ``. |
| `value` | yes in practice | any | `null` | The operand the extracted value is compared against. The expected type depends on `type` (a list for `ContainedIn`, a pattern string for `RegexMatch`, a number for `LessThan`, and so on). Omitting it compares against `null`; the outcome then depends on the condition type, so always set it explicitly. |
| `error_tolerance` | no | integer | `0` | The maximum provider-error severity this check tolerates. Errors at or below the tolerance mark the check as **skipped** instead of failed. See [Error tolerance](#error-tolerance-the-third-outcome). |

The supported condition types are:

`ContainedIn`, `Contains`, `Equals`, `GreaterThan`, `GreaterThanEqualTo`, `IsEmpty`, `IsNotEmpty`, `LessThan`, `LessThanEqualTo`, `NotContainedIn`, `NotContains`, `NotEquals`, `RegexMatch`

Their exact semantics are documented in the [evaluator reference](../tirith-reference/evaluators.md).

A provider may extract several values for one check (for example, one attribute per matching resource). The condition is applied to each value, and the check passes only if **every** value passes.

## `eval_expression`

A boolean expression that combines the per-check outcomes into the final verdict. Operands are evaluator `id`s; the operators are:

- `&&` — and
- `||` — or
- `!` — not
- `(` `)` — grouping

`&` and `|` are rejected with an explicit error (`Unsupported operator '&' in eval_expression. Use '&&' instead.`) and the run aborts with exit code `1`.

Two behaviors worth knowing:

- **An id that does not match any evaluator is silently dropped from the expression**, and the run continues. The result carries an informational note in its `errors` array (`The following evaluator ids are not defined and have been removed: ...`), but this is not a failure: a policy whose expression is `real_check && typo_id` passes if `real_check` passes. Check the `errors` array (or the `Errors:` block in the printed output) when authoring.
- **Skipped checks are removed from the expression** before it is evaluated, rather than being treated as false. `a && b` with `b` skipped evaluates as just `a`. If every id in the expression is removed — all checks skipped — the final verdict is neither pass nor fail; see the next section.

## Outcomes and exit codes

Every check has one of three outcomes, reported in the `passed` field of its result:

| `passed` | Meaning |
|---|---|
| `true` | Every value the provider extracted satisfied the condition. |
| `false` | At least one value failed the condition, the provider found no values at all (`Could not find input value`), or a provider error exceeded `error_tolerance`. |
| `null` | Skipped: the provider reported an error whose severity is within `error_tolerance`. |

The final verdict, `final_result`, is also tri-state: `true` when the expression evaluates true, `false` when it evaluates false, and `null` when every check it references was skipped.

The CLI exit code depends on `final_result` and the `--fail-on-error` flag:

| Situation | `final_result` | Exit (default) | Exit (`--fail-on-error`) |
|---|---|---|---|
| Policy passed | `true` | 0 | 0 |
| Policy failed | `false` | 0 | 3 |
| All checks skipped | `null` | 0 | 1 |
| Unresolved variable | absent | 0 | 1 |
| Policy file malformed (missing `meta`, `evaluators`, `eval_expression`, `id`, `provider_args`, `condition`; `&` instead of `&&` in the expression, and likewise for the or operator) | — | 1 | 1 |

Without `--fail-on-error` the exit code is `0` whether the policy passed or failed — the verdict is only in the output. A run where every check was skipped is deliberately treated as an error under `--fail-on-error`, not a pass: it verified nothing. See the [CLI reference](../tirith-usage/cli-reference.md) for the flag.

## Error tolerance: the third outcome

`error_tolerance` exists so a policy can tolerate *missing data* without tolerating *violations*. When a provider cannot extract a value, it reports an error with a numeric severity instead of a value. For each such error on a check:

- severity **>** `error_tolerance` → the check **fails**, with the provider's message.
- severity **≤** `error_tolerance` → that result is **skipped** (`passed: null`), with the provider's message.

The default tolerance is `0`. The severities the bundled providers use:

| Severity | Used by | Meaning |
|---|---|---|
| 0 | `terraform_plan` | No resource changes in the plan at all, or a matched resource has no planned attributes (for example, a resource being destroyed). Because the comparison is *strictly greater than*, severity-0 errors are skipped even at the default tolerance of 0. |
| 1 | `terraform_plan` | The resource type was not found in the plan. |
| 2 | `terraform_plan`, `json` | The attribute (`terraform_plan`) or `key_path` (`json`) was not found. |
| 99 | `terraform_plan` | The policy itself is malformed (unsupported `operation_type`, missing required argument). Do not set a tolerance this high: it would mask broken policies. |

So `"error_tolerance": 2` is the common setting for "skip this check when the key or attribute is absent", and `"error_tolerance": 1` for "skip when the resource type does not appear in the plan".

Two situations are never tolerated, regardless of the setting:

- The provider found **no values at all** for the check (`Could not find input value`) — this fails.
- The provider reported an error **without a severity**, which the engine treats as a malformed provider call — this fails.

A skipped check interacts with the final verdict as described above: it is removed from `eval_expression`, and if nothing is left, `final_result` is `null` — reported as `= Skipped final evaluator`, exit `0` by default and exit `1` under `--fail-on-error`.

## Variables

Any **string** value in the policy can be replaced by a variable reference:

```json
"condition": {
  "type": "LessThanEqualTo",
  "value": "{{ var.max_monthly_cost }}"
}
```

The rules, exactly as implemented:

- The syntax is `{{ var.NAME }}`. The `var.` prefix is mandatory; `{{ NAME }}` is not a variable reference and is left untouched.
- The reference must start the string, and the whole string is replaced by the variable's value — which keeps the variable's JSON type. A number stays a number, a list stays a list. Variables cannot be interpolated into the middle of a longer string.
- Substitution is applied to: string values directly under `meta`, each evaluator's `id`, string values directly under `provider_args` and `condition`, and `eval_expression`. It does **not** recurse into nested objects or arrays inside those keys.
- `NAME` may be a dotted path (`{{ var.limits.cost }}`), looked up inside the variable document.

Variables come from two CLI sources, applied in this order (later wins):

1. `-var-path vars.json` — a JSON object per file; the flag may be repeated, and files are merged left to right, so a later file overrides an earlier one key by key.
2. `-var NAME=VALUE` — `VALUE` is parsed as JSON (`-var 'max_monthly_cost=300'`, `-var 'env="prod"'`); the flag may be repeated. Inline variables override variable files. An inline variable that is not of the form `NAME=<valid JSON>` is ignored with a logged error — it does not define the variable.

If a referenced variable is not defined by any source, the policy is **not evaluated at all**: the result contains only `{"errors": ["Variables not found: NAME"]}`, there is no verdict, and the CLI exits `0` by default and `1` under `--fail-on-error`.

## Result document

With `--json`, the CLI prints a single JSON object:

| Key | Type | Content |
|---|---|---|
| `meta` | object | `version` and `required_provider` (always present, `null`/`"core"` when defaulted), plus whichever of `id`, `name`, `description`, `severity`, `enforcement`, `tags`, `remediation` the policy declared, copied verbatim. |
| `final_result` | `true` / `false` / `null` | The final verdict. |
| `evaluators` | array | One entry per check: `id`, `description`, tri-state `passed`, and `result` — the per-value messages, each with its own tri-state `passed`. |
| `errors` | array of strings | Informational notes from evaluating `eval_expression` (undefined ids that were removed, disallowed symbols). Empty on a clean run — including a clean *failing* run. |
| `eval_expression` | string | The expression that was evaluated, after variable substitution. |

For complete, runnable policies with their inputs and verdicts, see the [Policy Cookbook](./tirith-policy-cookbook.md).
